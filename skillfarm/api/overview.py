"""Overview API endpoints: Skillfarm characters of other users."""

# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI, Query

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from django.utils.translation import gettext as _

# Alliance Auth
from allianceauth.authentication.models import User

# AA Skillfarm
from skillfarm.api import schema
from skillfarm.api.characters import build_character_list
from skillfarm.api.helpers.core import can_view_overview
from skillfarm.helpers.lazy import get_character_portrait_url
from skillfarm.models.skillfarmaudit import SkillFarmAudit


def _serialize_overview_users(
    audits: QuerySet[SkillFarmAudit],
) -> list[schema.OverviewUserSchema]:
    """Group active audits by owning user and aggregate their state."""
    rows = audits.filter(active=True).values_list(
        "character__character_ownership__user_id",
        "is_training",
        "extractions_ready_count",
        "extraction_acknowledged",
    )

    stats: dict[int, dict[str, int]] = {}
    for user_id, is_training, ready_count, acknowledged in rows:
        if user_id is None:
            continue
        entry = stats.setdefault(
            user_id, {"total": 0, "training": 0, "paused": 0, "pending": 0}
        )
        entry["total"] += 1
        entry["training" if is_training else "paused"] += 1
        if ready_count > 0 and not acknowledged:
            entry["pending"] += 1

    users = User.objects.filter(id__in=stats.keys()).select_related(
        "profile__main_character"
    )

    result: list[schema.OverviewUserSchema] = []
    for user in users:
        main = getattr(getattr(user, "profile", None), "main_character", None)
        main_id = getattr(main, "character_id", None)
        entry = stats[user.id]
        result.append(
            schema.OverviewUserSchema(
                user_id=user.id,
                username=user.username,
                main_character_id=main_id,
                main_character_name=getattr(main, "character_name", user.username),
                corporation_name=getattr(main, "corporation_name", "") or "",
                corporation_ticker=getattr(main, "corporation_ticker", "") or "",
                portrait_url=(
                    get_character_portrait_url(main_id, size=64) if main_id else None
                ),
                character_count=entry["total"],
                training_count=entry["training"],
                paused_count=entry["paused"],
                pending_extractions_count=entry["pending"],
            )
        )

    return sorted(result, key=lambda item: item.main_character_name.lower())


class ApiEndpoints:
    tags = ["Overview"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "overview/",
            response={
                HTTPStatus.OK: schema.OverviewResponse,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="List all users with visible skillfarm characters",
        )
        def get_overview(request: WSGIRequest):
            if not can_view_overview(request.user):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audits = SkillFarmAudit.objects.visible_to(request.user)
            return schema.OverviewResponse(users=_serialize_overview_users(audits))

        @api.get(
            "overview/{user_id}/",
            response={
                HTTPStatus.OK: schema.OverviewUserCharactersResponse,
                HTTPStatus.FORBIDDEN: dict,
                HTTPStatus.NOT_FOUND: dict,
            },
            tags=self.tags,
            summary="Get the skillfarm characters of a single user",
        )
        def get_overview_user(
            request: WSGIRequest,
            user_id: int,
            filters: schema.CharacterFilter = Query(...),
        ):
            if not can_view_overview(request.user):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audits = SkillFarmAudit.objects.visible_to(request.user).filter(
                character__character_ownership__user_id=user_id
            )
            users = _serialize_overview_users(audits)
            if not users:
                return HTTPStatus.NOT_FOUND, {
                    "error": _("User not found or not accessible")
                }

            character_list = build_character_list(audits, filters)
            return schema.OverviewUserCharactersResponse(
                **character_list.model_dump(), user=users[0]
            )
