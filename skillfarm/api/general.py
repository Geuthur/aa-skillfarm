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
from skillfarm.api.helpers.core import can_view_overview
from skillfarm.helpers.lazy import get_character_portrait_url
from skillfarm.models.general import UserSettings


class ApiEndpoints:
    tags = ["General"]

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
                    name=_("Characters"),
                    link="/",
                ),
                schema.MenuLink(
                    name=_("Calculator"),
                    link="/calculator/",
                ),
            ]

            left_menu.append(
                schema.MenuLink(
                    name=_("Settings"),
                    link="/settings/",
                )
            )

            right_menu: list[schema.MenuLink] = []

            if can_view_overview(request.user):
                right_menu.append(
                    schema.MenuLink(
                        name=_("Overview"),
                        link="/overview/",
                    )
                )

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
                        link="/admin/",
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
