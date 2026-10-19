"""Superuser API endpoints for Skillfarm."""

# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Skillfarm
from skillfarm import __title__, tasks
from skillfarm.api import schema
from skillfarm.api.characters import _serialize_character_summary
from skillfarm.api.helpers.core import arabic_number_to_roman
from skillfarm.helpers.lazy import get_character_portrait_url
from skillfarm.models.skillfarmaudit import SkillFarmAudit, SkillFarmSetup
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


def _build_superuser_audit_schema(audit: SkillFarmAudit) -> schema.SuperuserAuditSchema:
    char = audit.character
    corp = getattr(char, "corporation", None)
    corp_id = getattr(char, "corporation_id", 0)
    corp_name = getattr(char, "corporation_name", "") or (
        corp.corporation_name if corp else ""
    )
    corp_ticker = getattr(char, "corporation_ticker", "") or (
        corp.corporation_ticker if corp else ""
    )

    ownership = getattr(char, "character_ownership", None)
    user_id = ownership.user_id if ownership else None
    user_name = ownership.user.username if ownership and ownership.user else None

    update_status_obj = audit.skillfarm_update_status.order_by("-last_run_at").first()
    if update_status_obj:
        if update_status_obj.has_token_error:
            status_str = "token_error"
        elif update_status_obj.is_success is False:
            status_str = "error"
        elif update_status_obj.is_success is True:
            status_str = "ok"
        else:
            status_str = "warning"
        last_update = (
            update_status_obj.last_run_finished_at.strftime("%Y-%m-%d %H:%M")
            if update_status_obj.last_run_finished_at
            else None
        )
        error_msg = update_status_obj.error_message or None
    else:
        status_str = "ok"
        last_update = None
        error_msg = None

    training_finish = (
        audit.training_finish_date.strftime("%Y-%m-%d %H:%M")
        if audit.training_finish_date
        else None
    )
    queue_finish = (
        audit.queue_finish_date.strftime("%Y-%m-%d %H:%M")
        if audit.queue_finish_date
        else None
    )

    return schema.SuperuserAuditSchema(
        character_id=char.character_id,
        character_name=char.character_name,
        corporation_id=corp_id,
        corporation_name=corp_name,
        corporation_ticker=corp_ticker,
        user_id=user_id,
        user_name=user_name,
        portrait_url=get_character_portrait_url(char.character_id, size=64),
        total_sp=audit.total_sp,
        is_training=audit.is_training,
        current_training_skill=audit.current_training_skill,
        training_finish_date=training_finish,
        queue_finish_date=queue_finish,
        extractions_ready_count=audit.extractions_ready_count,
        active=audit.active,
        status=status_str,
        last_update=last_update,
        error_message=error_msg,
    )


class ApiEndpoints:
    tags = ["Superuser"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "superuser/audits/",
            response={
                HTTPStatus.OK: list[schema.SuperuserAuditSchema],
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="List all Skillfarm character audits across the system for superusers",
        )
        def list_all_audits(request: WSGIRequest):
            if not request.user.is_superuser:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audits = (
                SkillFarmAudit.objects.select_related(
                    "character",
                    "character__character_ownership__user",
                )
                .prefetch_related("skillfarm_update_status")
                .all()
                .order_by("character__character_name")
            )
            return [_build_superuser_audit_schema(audit) for audit in audits]

        @api.post(
            "superuser/audits/{int:character_id}/update/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Trigger single character update task for superusers",
        )
        def trigger_audit_update(
            request: WSGIRequest,
            character_id: int,
            payload: schema.SuperuserAuditUpdateRequest | None = None,
        ):
            if not request.user.is_superuser:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audit = get_object_or_404(
                SkillFarmAudit.objects.select_related("character"),
                character__character_id=character_id,
            )

            force = payload.force_refresh if payload else False
            tasks.update_character.apply_async(
                args=[audit.pk],
                kwargs={"force_refresh": force},
                priority=7,
            )

            logger.info(
                "Superuser %s triggered update for character %s (force=%s)",
                request.user,
                audit.character.character_name,
                force,
            )

            return schema.ActionResponse(
                success=True,
                message=_("Queued update task for %(name)s (force_refresh=%(force)s)")
                % {
                    "name": audit.character.character_name,
                    "force": force,
                },
            )

        @api.delete(
            "superuser/audits/{int:character_id}/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Delete a character audit permanently for superusers",
        )
        def delete_audit(request: WSGIRequest, character_id: int):
            if not request.user.is_superuser:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audit = get_object_or_404(
                SkillFarmAudit.objects.select_related("character"),
                character__character_id=character_id,
            )

            char_name = audit.character.character_name
            audit.delete()

            logger.info(
                "Superuser %s deleted character audit %s (id=%s)",
                request.user,
                char_name,
                character_id,
            )

            return schema.ActionResponse(
                success=True,
                message=_("Successfully deleted %(name)s from Skillfarm")
                % {"name": char_name},
            )

        @api.get(
            "superuser/audits/{int:character_id}/inspect/",
            response={
                HTTPStatus.OK: schema.CharacterDetailResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Get character detailed inspection view for superusers",
        )
        # pylint: disable=too-many-locals
        def inspect_audit(request: WSGIRequest, character_id: int):
            if not request.user.is_superuser:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audit = get_object_or_404(
                SkillFarmAudit.objects.select_related(
                    "character",
                ).prefetch_related(
                    "skillfarm_update_status",
                    "skillfarm_skillqueue",
                    "skillfarm_skillqueue__eve_type",
                ),
                character__character_id=character_id,
            )

            setup = SkillFarmSetup.objects.filter(character=audit).first()
            skillset = setup.skillset if setup and setup.skillset else []

            now = timezone.now()
            serialized_queue: list[schema.SkillQueueEntrySchema] = []
            queue_qs = (
                audit.skillfarm_skillqueue.select_related("eve_type")
                .all()
                .order_by("queue_position")
            )

            for entry in queue_qs:
                progress = 0.0
                if (
                    entry.start_date
                    and entry.finish_date
                    and entry.start_date <= now <= entry.finish_date
                ):
                    total_sec = (entry.finish_date - entry.start_date).total_seconds()
                    if total_sec > 0:
                        elapsed = (now - entry.start_date).total_seconds()
                        progress = round(
                            max(0.0, min(100.0, (elapsed / total_sec) * 100.0)), 1
                        )

                is_active = bool(
                    entry.start_date
                    and entry.finish_date
                    and entry.start_date <= now <= entry.finish_date
                )
                is_extractable = bool(
                    entry.finish_date
                    and entry.finished_level == 5
                    and entry.finish_date <= now
                    and entry.eve_type.name in skillset
                )

                serialized_queue.append(
                    schema.SkillQueueEntrySchema(
                        skill_id=entry.eve_type.id,
                        skill_name=entry.eve_type.name,
                        finished_level=entry.finished_level,
                        finished_level_roman=arabic_number_to_roman(
                            entry.finished_level
                        ),
                        queue_position=entry.queue_position,
                        start_date=(
                            entry.start_date.strftime("%Y-%m-%d %H:%M")
                            if entry.start_date
                            else None
                        ),
                        finish_date=(
                            entry.finish_date.strftime("%Y-%m-%d %H:%M")
                            if entry.finish_date
                            else None
                        ),
                        start_sp=entry.level_start_sp or 0,
                        end_sp=entry.level_end_sp or 0,
                        training_start_sp=entry.training_start_sp or 0,
                        progress_percent=progress,
                        is_active=is_active,
                        is_extractable=is_extractable,
                    )
                )

            farmed_skills_qs = (
                audit.skillfarm_skills.filter(eve_type__name__in=skillset)
                .select_related("eve_type")
                .order_by("eve_type__name")
            )

            serialized_farmed: list[schema.FarmedSkillSchema] = [
                schema.FarmedSkillSchema(
                    skill_id=s.eve_type.id,
                    skill_name=s.eve_type.name,
                    active_level=s.active_skill_level,
                    trained_level=s.trained_skill_level,
                    skillpoints=s.skillpoints_in_skill,
                    is_extractable=(s.trained_skill_level == 5),
                )
                for s in farmed_skills_qs
            ]

            return schema.CharacterDetailResponse(
                character=_serialize_character_summary(audit),
                skillqueue=serialized_queue,
                farmed_skills=serialized_farmed,
                configured_skillset=skillset,
            )
