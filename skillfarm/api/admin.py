"""Administration API endpoints for Skillfarm V2."""

# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI, Schema

# Django
from django.db.models import Sum
from django.utils.translation import gettext as _

# AA Skillfarm
from skillfarm import tasks
from skillfarm.api import schema
from skillfarm.models.skillfarmaudit import SkillFarmAudit


class AdminStatsResponse(Schema):
    total_characters: int
    active_characters: int
    in_training_count: int
    paused_training_count: int
    total_sp: int
    total_pending_extractions: int


class AdminUpdateRequest(Schema):
    force_refresh: bool = False


class ApiEndpoints:
    tags = ["Administration"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "admin/stats/",
            response={
                HTTPStatus.OK: AdminStatsResponse,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Get administrative statistics for all Skillfarm characters",
        )
        def get_admin_stats(request):
            if not (
                request.user.is_superuser
                or request.user.has_perm("skillfarm.admin_access")
            ):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

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
            "admin/update-all/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Queue full update task for all Skillfarm characters",
        )
        def trigger_update_all(request, payload: AdminUpdateRequest | None = None):
            if not (
                request.user.is_superuser
                or request.user.has_perm("skillfarm.admin_access")
            ):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

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
            "admin/update-prices/",
            response={
                HTTPStatus.OK: schema.ActionResponse,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Queue market prices update task",
        )
        def trigger_update_prices(request):
            if not (
                request.user.is_superuser
                or request.user.has_perm("skillfarm.admin_access")
            ):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            tasks.update_all_prices.apply_async()

            return schema.ActionResponse(
                success=True,
                message=_("Queued market price update task"),
            )
