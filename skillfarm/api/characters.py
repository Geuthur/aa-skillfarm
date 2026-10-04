"""Character API endpoints for Skillfarm V2."""

# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI, Query

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Skillfarm
from skillfarm import __title__
from skillfarm.api import schema
from skillfarm.api.helpers.core import arabic_number_to_roman, get_skillfarm_character
from skillfarm.helpers.lazy import get_character_portrait_url
from skillfarm.models.skillfarmaudit import (
    SkillFarmAudit,
    SkillFarmSetup,
)
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


# pylint: disable=too-many-locals
def _serialize_character_summary(
    audit: SkillFarmAudit,
) -> schema.CharacterSummarySchema:
    char = audit.character
    corp = getattr(char, "corporation", None)
    corp_id = getattr(char, "corporation_id", 0)
    corp_name = getattr(char, "corporation_name", "") or (
        corp.corporation_name if corp else ""
    )
    corp_ticker = getattr(char, "corporation_ticker", "") or (
        corp.corporation_ticker if corp else ""
    )

    # Determine update status
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
    else:
        status_str = "ok"
        last_update = None

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
    ack_at = (
        audit.extraction_acknowledged_at.strftime("%Y-%m-%d %H:%M")
        if audit.extraction_acknowledged_at
        else None
    )

    training_start = None
    progress_percent = 0.0
    now = timezone.now()

    if audit.is_training:
        active_skill = audit.skillfarm_skillqueue.filter(
            start_date__lte=now, finish_date__gt=now
        ).first()
        if active_skill:
            if active_skill.start_date:
                training_start = active_skill.start_date.strftime("%Y-%m-%d %H:%M")
            if active_skill.start_date and active_skill.finish_date:
                total_duration = (
                    active_skill.finish_date - active_skill.start_date
                ).total_seconds()
                if total_duration > 0:
                    elapsed = (now - active_skill.start_date).total_seconds()
                    progress_percent = round(
                        max(0.0, min(100.0, (elapsed / total_duration) * 100.0)), 1
                    )

    return schema.CharacterSummarySchema(
        character_id=char.character_id,
        character_name=char.character_name,
        corporation_id=corp_id,
        corporation_name=corp_name,
        corporation_ticker=corp_ticker,
        portrait_url=get_character_portrait_url(char.character_id, size=64),
        total_sp=audit.total_sp,
        is_training=audit.is_training,
        training_start_date=training_start,
        training_finish_date=training_finish,
        queue_finish_date=queue_finish,
        current_training_skill=audit.current_training_skill,
        progress_percent=progress_percent,
        extractions_ready_count=audit.extractions_ready_count,
        extraction_acknowledged=audit.extraction_acknowledged,
        extraction_acknowledged_at=ack_at,
        queue_paused_acknowledged=audit.queue_paused_acknowledged,
        notification_enabled=audit.notification,
        update_status=status_str,
        last_update=last_update,
    )


def build_character_list(
    audits: QuerySet[SkillFarmAudit], filters: schema.CharacterFilter
) -> schema.CharacterListResponse:
    """Build the character list payload (counters over `audits`, list filtered)."""
    audits = (
        audits.filter(active=True)
        .select_related("character")
        .prefetch_related("skillfarm_update_status", "skillfarm_skillqueue")
    )

    total_count = audits.count()
    paused_count = audits.filter(is_training=False).count()
    pending_extractions = audits.filter(
        extractions_ready_count__gt=0, extraction_acknowledged=False
    ).count()
    acknowledged_extractions = audits.filter(
        extractions_ready_count__gt=0, extraction_acknowledged=True
    ).count()

    filtered_audits = audits.filter_by_schema(filters).order_by(
        "-extractions_ready_count",
        "is_training",
        "character__character_name",
    )

    return schema.CharacterListResponse(
        characters=[_serialize_character_summary(audit) for audit in filtered_audits],
        total_count=total_count,
        paused_training_count=paused_count,
        pending_extractions_count=pending_extractions,
        acknowledged_extractions_count=acknowledged_extractions,
    )


class ApiEndpoints:
    tags = ["Characters"]

    def __init__(self, api: NinjaAPI):
        self.register_endpoints(api)
        self.register_modifications(api)

    def register_endpoints(self, api: NinjaAPI):
        @api.get(
            "characters/",
            response={
                HTTPStatus.OK: schema.CharacterListResponse,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="List skillfarm characters with filterable metrics",
        )
        def list_characters(
            request: WSGIRequest,
            filters: schema.CharacterFilter = Query(...),
        ):
            if not request.user.has_perm("skillfarm.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            characters = SkillFarmAudit.objects.owned_by(request.user)
            return build_character_list(characters, filters)

        @api.get(
            "characters/{character_id}/",
            response={
                HTTPStatus.OK: schema.CharacterDetailResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Get character details including skillqueue and farm setup",
        )
        # pylint: disable=too-many-locals
        def get_character_detail(request: WSGIRequest, character_id: int):
            perms, audit = get_skillfarm_character(request, character_id)

            if audit is None:
                return HTTPStatus.NOT_FOUND, {
                    "error": _("Character not found or not accessible")
                }

            if perms is False:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            # Configured skillset
            try:
                setup = audit.skillfarm_setup
                skillset = setup.skillset or []
            except SkillFarmSetup.DoesNotExist:
                skillset = []

            now = timezone.now()

            # Skill Queue Entries
            queue_entries = (
                audit.skillfarm_skillqueue.all()
                .select_related("eve_type")
                .order_by("queue_position")
            )
            serialized_queue: list[schema.SkillQueueEntrySchema] = []

            for entry in queue_entries:
                diff = (entry.level_end_sp or 0) - (entry.level_start_sp or 0)
                if diff > 0 and entry.training_start_sp:
                    progress = round(
                        ((entry.training_start_sp - (entry.level_start_sp or 0)) / diff)
                        * 100.0,
                        2,
                    )
                else:
                    progress = 0.0
                progress = max(0.0, min(100.0, progress))

                is_active = bool(
                    entry.start_date
                    and entry.finish_date
                    and entry.start_date <= now < entry.finish_date
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

            # Farmed Skills
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

    def register_modifications(self, api: NinjaAPI):
        @api.post(
            "characters/{character_id}/acknowledge-extractions/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Acknowledge ready skill extractions for a character",
        )
        def acknowledge_extractions(request: WSGIRequest, character_id: int):
            perms, audit = get_skillfarm_character(request, character_id, manage=True)

            if audit is None:
                return HTTPStatus.NOT_FOUND, {
                    "error": _("Character not found or not accessible")
                }

            if perms is False:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audit.acknowledge_extractions(request.user)
            logger.info("User %s acknowledged extractions for %s", request.user, audit)

            return schema.ActionResponse(
                success=True,
                message=_("Extractions successfully marked as reviewed/acknowledged"),
            )

        @api.post(
            "characters/{character_id}/acknowledge-paused/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Acknowledge paused or empty queue for a character",
        )
        def acknowledge_paused(request: WSGIRequest, character_id: int):
            perms, audit = get_skillfarm_character(request, character_id, manage=True)

            if audit is None:
                return HTTPStatus.NOT_FOUND, {
                    "error": _("Character not found or not accessible")
                }

            if perms is False:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audit.acknowledge_queue_paused()
            logger.info("User %s acknowledged paused queue for %s", request.user, audit)

            return schema.ActionResponse(
                success=True,
                message=_("Inactive training status acknowledged"),
            )

        @api.post(
            "characters/{character_id}/toggle-notification/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Toggle notifications for a character",
        )
        def toggle_notification(request: WSGIRequest, character_id: int):
            perms, audit = get_skillfarm_character(request, character_id, manage=True)

            if audit is None:
                return HTTPStatus.NOT_FOUND, {
                    "error": _("Character not found or not accessible")
                }

            if perms is False:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audit.notification = not audit.notification
            audit.save(update_fields=["notification"])
            status_text = _("enabled") if audit.notification else _("disabled")

            return schema.ActionResponse(
                success=True,
                message=_("Notifications %s for %s")
                % (status_text, audit.character.character_name),
            )

        @api.get(
            "characters/{character_id}/setup/",
            response={
                HTTPStatus.OK: schema.SkillSetupSchema,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Get configured skillset for character",
        )
        def get_skillsetup(request: WSGIRequest, character_id: int):
            perms, audit = get_skillfarm_character(request, character_id, manage=True)

            if audit is None:
                return HTTPStatus.NOT_FOUND, {
                    "error": _("Character not found or not accessible")
                }

            if perms is False:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            setup = SkillFarmSetup.objects.get_or_create(character=audit)[0]
            skillset = setup.skillset or []

            # Available trained skills on this character that can be configured
            available = list(
                audit.skillfarm_skills.filter(trained_skill_level__gte=1)
                .values_list("eve_type__name", flat=True)
                .distinct()
                .order_by("eve_type__name")
            )

            return schema.SkillSetupSchema(
                character_id=audit.character.character_id,
                character_name=audit.character.character_name,
                skillset=skillset,
                available_skills=available,
            )

        @api.post(
            "characters/{character_id}/setup/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Update configured skillset for character",
        )
        def update_skillsetup(
            request: WSGIRequest,
            character_id: int,
            payload: schema.SkillSetupUpdateRequest,
        ):
            perms, audit = get_skillfarm_character(request, character_id, manage=True)

            if audit is None:
                return HTTPStatus.NOT_FOUND, {
                    "error": _("Character not found or not accessible")
                }

            if perms is False:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            setup = SkillFarmSetup.objects.get_or_create(character=audit)[0]
            setup.skillset = payload.selected_skills
            setup.save()

            # Recalculate extractions with new skillset
            audit.update_training_and_extraction_state()

            return schema.ActionResponse(
                success=True,
                message=_("Skillset successfully updated for %s")
                % audit.character.character_name,
            )

        @api.delete(
            "characters/{character_id}/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Remove character from skillfarm",
        )
        def delete_character(request: WSGIRequest, character_id: int):
            perms, audit = get_skillfarm_character(request, character_id, manage=True)

            if audit is None:
                return HTTPStatus.NOT_FOUND, {
                    "error": _("Character not found or not accessible")
                }

            if perms is False:
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            char_name = audit.character.character_name
            audit.delete()
            logger.info(
                "User %s deleted character %s from Skillfarm", request.user, char_name
            )

            return schema.ActionResponse(
                success=True,
                message=_("%s successfully removed from Skillfarm") % char_name,
            )

        @api.post(
            "acknowledge-all-extractions/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Bulk acknowledge all pending ready extractions",
        )
        def acknowledge_all_extractions(request: WSGIRequest):
            if not request.user.has_perm("skillfarm.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audits = SkillFarmAudit.objects.owned_by(request.user).filter(
                active=True,
                extractions_ready_count__gt=0,
                extraction_acknowledged=False,
            )
            count = audits.count()
            audits.update(
                extraction_acknowledged=True,
                extraction_acknowledged_at=timezone.now(),
                extraction_acknowledged_by=request.user,
            )
            logger.info("User %s bulk acknowledged %d characters", request.user, count)

            return schema.ActionResponse(
                success=True,
                message=_("Successfully acknowledged extractions for %d characters")
                % count,
            )
