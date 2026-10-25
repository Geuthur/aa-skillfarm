"""Administration API endpoints for Skillfarm."""

# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.eveonline.evelinks.eveimageserver import corporation_logo_url
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger

# AA Skillfarm
from skillfarm import __title__, tasks
from skillfarm.api import schema
from skillfarm.api.characters import _serialize_character_summary
from skillfarm.api.helpers.core import arabic_number_to_roman
from skillfarm.helpers.lazy import get_character_portrait_url
from skillfarm.models.general import General
from skillfarm.models.skillfarmaudit import SkillFarmAudit, SkillFarmSetup
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


# pylint: disable=too-many-locals
def _build_administration_audit_schema(
    audit: SkillFarmAudit,
) -> schema.AdministrationAuditSchema:
    char = audit.character
    corp_id = getattr(char, "corporation_id", 0)
    corp_name = getattr(char, "corporation_name", "")
    corp_ticker = getattr(char, "corporation_ticker", "")

    ownership = getattr(char, "character_ownership", None)
    user_id = ownership.user_id if ownership else None
    user = ownership.user if ownership else None
    user_name = user.username if user else None

    main = getattr(getattr(user, "profile", None), "main_character", None)
    main_char_id = getattr(main, "character_id", None)
    main_char_name = (
        getattr(main, "character_name", None) or user_name or char.character_name
    )
    main_portrait = (
        get_character_portrait_url(main_char_id, size=64) if main_char_id else None
    )

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

    return schema.AdministrationAuditSchema(
        character_id=char.character_id,
        character_name=char.character_name,
        corporation_id=corp_id,
        corporation_name=corp_name,
        corporation_ticker=corp_ticker,
        user_id=user_id,
        user_name=user_name,
        main_character_id=main_char_id,
        main_character_name=main_char_name,
        main_portrait_url=main_portrait,
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


class AdminStatsResponse(Schema):
    total_characters: int
    active_characters: int
    in_training_count: int
    paused_training_count: int
    total_sp: int
    total_pending_extractions: int


class AdminUpdateRequest(Schema):
    force_refresh: bool = False


def _administration_denied() -> dict:
    return {"error": _("Administration permission required.")}


# Corporation IDs below this value belong to NPC corporations
MIN_PLAYER_CORPORATION_ID = 10_000_000


def _superuser_denied() -> dict:
    return {"error": _("Superuser permission required.")}


def _corporations_denied() -> dict:
    return {"error": _("Corporation access permission required.")}


class ApiEndpoints:
    tags = ["Administration"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "administration/audits/",
            response={
                HTTPStatus.OK: list[schema.AdministrationAuditSchema],
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="List all Skillfarm character audits across the system for administrators",
        )
        def list_all_audits(request: WSGIRequest):
            if not General.has_administration_access(request.user):
                return HTTPStatus.FORBIDDEN, _administration_denied()

            audits = (
                SkillFarmAudit.objects.select_related(
                    "character",
                    "character__character_ownership__user",
                    "character__character_ownership__user__profile__main_character",
                )
                .prefetch_related("skillfarm_update_status")
                .all()
                .order_by("character__character_name")
            )
            return [_build_administration_audit_schema(audit) for audit in audits]

        @api.post(
            "administration/audits/{int:character_id}/update/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Trigger single character update task for administrators",
        )
        def trigger_audit_update(
            request: WSGIRequest,
            character_id: int,
            payload: schema.AdministrationAuditUpdateRequest | None = None,
        ):
            if not General.has_administration_access(request.user):
                return HTTPStatus.FORBIDDEN, _administration_denied()

            audit = get_object_or_404(
                SkillFarmAudit.objects.select_related("character"),
                character__character_id=character_id,
            )

            force = payload.force_refresh if payload else False
            if force and not General.is_superuser_only(request.user):
                return HTTPStatus.FORBIDDEN, _superuser_denied()

            tasks.update_character.apply_async(
                args=[audit.pk],
                kwargs={"force_refresh": force},
                priority=7,
            )

            logger.info(
                "Administrator %s triggered update for character %s (force=%s)",
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
            "administration/audits/{int:character_id}/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Delete a character audit permanently (superusers only)",
        )
        def delete_audit(request: WSGIRequest, character_id: int):
            if not General.is_superuser_only(request.user):
                return HTTPStatus.FORBIDDEN, _superuser_denied()

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
            "administration/audits/{int:character_id}/inspect/",
            response={
                HTTPStatus.OK: schema.CharacterDetailResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Get character detailed inspection view for administrators",
        )
        # pylint: disable=too-many-locals
        def inspect_audit(request: WSGIRequest, character_id: int):
            if not General.has_administration_access(request.user):
                return HTTPStatus.FORBIDDEN, _administration_denied()

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

        @api.get(
            "administration/stats/",
            response={
                HTTPStatus.OK: AdminStatsResponse,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Get administrative statistics for all Skillfarm characters",
        )
        def get_admin_stats(request):
            if not General.has_administration_access(request.user):
                return HTTPStatus.FORBIDDEN, _administration_denied()

            qs = SkillFarmAudit.objects.all()
            total_chars = qs.count()
            active_chars = qs.filter(active=True).count()
            in_training = qs.filter(active=True, is_training=True).count()
            paused = qs.filter(active=True, is_training=False).count()
            total_sp = (
                qs.filter(active=True).aggregate(total=Sum("total_sp"))["total"] or 0
            )
            pending_extractions = (
                qs.filter(
                    active=True,
                    extractions_ready_count__gt=0,
                    extraction_acknowledged=False,
                ).aggregate(total=Sum("extractions_ready_count"))["total"]
                or 0
            )

            return AdminStatsResponse(
                total_characters=total_chars,
                active_characters=active_chars,
                in_training_count=in_training,
                paused_training_count=paused,
                total_sp=total_sp,
                total_pending_extractions=pending_extractions,
            )

        @api.post(
            "administration/update-all/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Queue full update task for all Skillfarm characters (superusers only)",
        )
        def trigger_update_all(request, payload: AdminUpdateRequest | None = None):
            if not General.is_superuser_only(request.user):
                return HTTPStatus.FORBIDDEN, _superuser_denied()

            force = payload.force_refresh if payload else False
            tasks.update_all_skillfarm.apply_async(
                kwargs={"force_refresh": force}, priority=7
            )

            return schema.ActionResponse(
                success=True,
                message=_(
                    "Queued Skillfarm update task for all characters (force_refresh=%s)"
                )
                % force,
            )

        @api.post(
            "administration/update-prices/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Queue market prices update task (superusers only)",
        )
        def trigger_update_prices(request):
            if not General.is_superuser_only(request.user):
                return HTTPStatus.FORBIDDEN, _superuser_denied()

            tasks.update_all_prices.apply_async()

            return schema.ActionResponse(
                success=True,
                message=_("Queued market price update task"),
            )

        @api.get(
            "administration/corporations/",
            response={
                HTTPStatus.OK: list[schema.AdministrationCorporationSchema],
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="List corporations with registered characters and their unregistered character counts",
        )
        def list_corporations(request: WSGIRequest):
            has_access, sees_all, own_corp_id = General.get_corporation_scope(
                request.user
            )
            if not has_access:
                return HTTPStatus.FORBIDDEN, _corporations_denied()

            # NPC corporations (ID below 10,000,000) can not have tokens
            corporations = EveCorporationInfo.objects.filter(
                corporation_id__gte=MIN_PLAYER_CORPORATION_ID
            )
            if not sees_all:
                corporations = corporations.filter(corporation_id=own_corp_id)

            corp_ids = list(corporations.values_list("corporation_id", flat=True))
            known = dict(
                EveCharacter.objects.filter(corporation_id__in=corp_ids)
                .values_list("corporation_id")
                .annotate(total=Count("pk"))
            )
            registered = dict(
                EveCharacter.objects.filter(
                    corporation_id__in=corp_ids,
                    skillfarm_character__isnull=False,
                )
                .values_list("corporation_id")
                .annotate(total=Count("pk"))
            )

            result = []
            for corp in corporations.order_by("corporation_name"):
                total = known.get(corp.corporation_id, 0)
                reg = registered.get(corp.corporation_id, 0)
                # Corporations without any registered character are not listed
                if reg == 0:
                    continue
                result.append(
                    schema.AdministrationCorporationSchema(
                        corporation_id=corp.corporation_id,
                        corporation_name=corp.corporation_name,
                        corporation_ticker=corp.corporation_ticker,
                        logo_url=corporation_logo_url(corp.corporation_id, size=64),
                        registered_count=reg,
                        unregistered_count=total - reg,
                    )
                )
            return result

        @api.get(
            "administration/corporations/{int:corporation_id}/unregistered/",
            response={
                HTTPStatus.OK: schema.AdministrationUnregisteredResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="List characters of a corporation that are not registered in Skillfarm",
        )
        def list_corporation_unregistered(request: WSGIRequest, corporation_id: int):
            has_access, sees_all, own_corp_id = General.get_corporation_scope(
                request.user
            )
            if not has_access:
                return HTTPStatus.FORBIDDEN, _corporations_denied()

            if not EveCorporationInfo.objects.filter(
                corporation_id=corporation_id,
                corporation_id__gte=MIN_PLAYER_CORPORATION_ID,
            ).exists():
                return HTTPStatus.NOT_FOUND, {"error": _("Corporation not found.")}

            if not sees_all and corporation_id != own_corp_id:
                return HTTPStatus.FORBIDDEN, _corporations_denied()

            characters = (
                EveCharacter.objects.filter(corporation_id=corporation_id)
                .filter(skillfarm_character__isnull=True)
                .order_by("character_name")
            )
            items = [
                schema.UnregisteredCharacterSchema(
                    id=char.character_id,
                    name=char.character_name,
                    avatar_url=get_character_portrait_url(char.character_id, size=64),
                    subtitle=char.corporation_name,
                )
                for char in characters
            ]
            return schema.AdministrationUnregisteredResponse(
                corporation_id=corporation_id, items=items
            )
