"""General API endpoints: User data and Menu navigation."""

# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
from django.utils.translation import gettext as _

# AA Skillfarm
from skillfarm.api import schema
from skillfarm.helpers.lazy import get_character_portrait_url
from skillfarm.models.general import UserSettings
from skillfarm.models.helpers.update_manager import CharacterUpdateSection
from skillfarm.models.skillfarmaudit import SkillFarmAudit


class ApiEndpoints:
    tags = ["General"]

    # pylint: disable=too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "menu/",
            response={
                HTTPStatus.OK: schema.MenuSchema,
            },
            tags=self.tags,
            summary="Get Skillfarm navigation menu",
        )
        def get_menu(request: WSGIRequest):
            left_menu: list[schema.MenuLink] = [
                schema.MenuLink(
                    name=_("Overview"),
                    link="/",
                ),
                schema.MenuLink(
                    name=_("My Characters"),
                    link="/characters/",
                ),
                schema.MenuLink(
                    name=_("Calculator"),
                    link="/calculator/",
                ),
            ]

            has_user_char_errors = False
            error_count = 0
            if request.user.is_authenticated:
                user_audits = (
                    SkillFarmAudit.objects.owned_by(request.user)
                    .filter(active=True)
                    .prefetch_related("skillfarm_update_status")
                )
                for audit in user_audits:
                    if audit.get_status.value in ("error", "token_error"):
                        has_user_char_errors = True
                        error_count += 1

            left_menu.append(
                schema.MenuLink(
                    name=_("Settings"),
                    link="/settings/",
                    badge=error_count if error_count > 0 else None,
                    has_errors=has_user_char_errors,
                )
            )

            right_menu: list[schema.MenuLink] = []

            right_menu.append(
                schema.MenuLink(
                    name=_("Add Character"),
                    link=reverse("skillfarm:add_char"),
                    is_external=True,
                )
            )

            if request.user.is_superuser:
                right_menu.append(
                    schema.MenuLink(
                        name=_("Superuser"),
                        link="/superuser/",
                    )
                )

            return schema.MenuSchema(
                left_links=left_menu,
                right_links=right_menu,
            )

        @api.get(
            "user/",
            response={
                HTTPStatus.OK: schema.UserData,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Get current user data and permissions",
        )
        def get_user(request: WSGIRequest):
            if not request.user.has_perm("skillfarm.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            main_char = getattr(
                getattr(request.user, "profile", None), "main_character", None
            )

            char_id = getattr(main_char, "character_id", 0)
            char_name = getattr(main_char, "character_name", request.user.username)
            corp_id = getattr(main_char, "corporation_id", 0)
            corp_name = getattr(main_char, "corporation_name", "")
            alliance_id = getattr(main_char, "alliance_id", None)
            alliance_name = getattr(main_char, "alliance_name", None)

            portrait = get_character_portrait_url(char_id, size=64) if char_id else None

            is_admin = request.user.is_superuser or request.user.has_perm(
                "skillfarm.admin_access"
            )

            return schema.UserData(
                user_id=request.user.id,
                character_id=char_id,
                character_name=char_name,
                corporation_id=corp_id,
                corporation_name=corp_name,
                alliance_id=alliance_id,
                alliance_name=alliance_name,
                portrait=portrait,
                is_admin=is_admin,
                has_corp_access=request.user.has_perm("skillfarm.corp_access"),
            )

        @api.get(
            "settings/",
            response={
                HTTPStatus.OK: schema.UserSettingsSchema,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Get current user's Skillfarm settings",
        )
        def get_user_settings(request: WSGIRequest):
            if not request.user.has_perm("skillfarm.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            user_settings = UserSettings.objects.get_or_create(user=request.user)[0]
            return schema.UserSettingsSchema(
                disable_notifications=user_settings.disable_notifications
            )

        @api.put(
            "settings/",
            response={
                HTTPStatus.OK: schema.UserSettingsSchema,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Update current user's Skillfarm settings",
        )
        def update_user_settings(
            request: WSGIRequest, payload: schema.UserSettingsUpdateRequest
        ):
            if not request.user.has_perm("skillfarm.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            user_settings = UserSettings.objects.get_or_create(user=request.user)[0]
            user_settings.disable_notifications = payload.disable_notifications
            user_settings.save(update_fields=["disable_notifications"])
            return schema.UserSettingsSchema(
                disable_notifications=user_settings.disable_notifications
            )

        @api.get(
            "user/characters/status/",
            response={
                HTTPStatus.OK: list[schema.UserCharacterStatusSchema],
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Get current user's character update statuses for settings overview",
        )
        # pylint: disable=too-many-locals
        def get_user_character_statuses(request: WSGIRequest):
            if not request.user.has_perm("skillfarm.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            audits = (
                SkillFarmAudit.objects.owned_by(request.user)
                .select_related("character")
                .prefetch_related("skillfarm_update_status")
                .order_by("character__character_name")
            )

            result: list[schema.UserCharacterStatusSchema] = []
            for audit in audits:
                char = audit.character
                corp = getattr(char, "corporation", None)
                corp_id = getattr(char, "corporation_id", 0)
                corp_name = getattr(char, "corporation_name", "") or (
                    corp.corporation_name if corp else ""
                )
                corp_ticker = getattr(char, "corporation_ticker", "") or (
                    corp.corporation_ticker if corp else ""
                )

                status_val = audit.get_status.value
                has_error = status_val in ("error", "token_error")

                sections_dict = {
                    s.section: s for s in audit.skillfarm_update_status.all()
                }

                section_list: list[schema.UserCharacterStatusSectionSchema] = []
                last_finished_dt = None
                latest_error_message = None

                for sec in CharacterUpdateSection:
                    status_obj = sections_dict.get(sec.value)
                    if status_obj:
                        if status_obj.last_run_finished_at and (
                            last_finished_dt is None
                            or status_obj.last_run_finished_at > last_finished_dt
                        ):
                            last_finished_dt = status_obj.last_run_finished_at

                        if status_obj.error_message and not latest_error_message:
                            latest_error_message = status_obj.error_message

                        section_list.append(
                            schema.UserCharacterStatusSectionSchema(
                                section=sec.value,
                                section_name=str(sec.label),
                                is_success=status_obj.is_success,
                                has_token_error=status_obj.has_token_error,
                                error_message=status_obj.error_message or None,
                                last_run_at=(
                                    status_obj.last_run_at.strftime("%Y-%m-%d %H:%M")
                                    if status_obj.last_run_at
                                    else None
                                ),
                                last_run_finished_at=(
                                    status_obj.last_run_finished_at.strftime(
                                        "%Y-%m-%d %H:%M"
                                    )
                                    if status_obj.last_run_finished_at
                                    else None
                                ),
                            )
                        )
                    else:
                        section_list.append(
                            schema.UserCharacterStatusSectionSchema(
                                section=sec.value,
                                section_name=str(sec.label),
                                is_success=None,
                                has_token_error=False,
                                error_message=None,
                                last_run_at=None,
                                last_run_finished_at=None,
                            )
                        )

                last_sync = (
                    last_finished_dt.strftime("%Y-%m-%d %H:%M")
                    if last_finished_dt
                    else None
                )

                result.append(
                    schema.UserCharacterStatusSchema(
                        character_id=char.character_id,
                        character_name=char.character_name,
                        corporation_id=corp_id,
                        corporation_name=corp_name,
                        corporation_ticker=corp_ticker,
                        portrait_url=get_character_portrait_url(
                            char.character_id, size=64
                        ),
                        status=status_val,
                        has_error=has_error,
                        is_active=audit.active,
                        last_sync=last_sync,
                        error_message=latest_error_message,
                        notification_enabled=audit.notification,
                        sections=section_list,
                    )
                )

            return result
