"""Hook into Alliance Auth"""

# Django
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from . import app_settings, urls
from .models.general import General


class SkillfarmMenuItem(MenuItemHook):
    """This class ensures only authorized users will see the menu entry"""

    def __init__(self):
        super().__init__(
            f"{app_settings.SKILLFARM_APP_NAME}",
            "fas fa-book-medical fa-fw",
            "skillfarm:react_base",
            navactive=["skillfarm:"],
        )

    def render(self, request):
        if General.has_basic_access(request.user):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_menu():
    """Register the menu item"""

    return SkillfarmMenuItem()


@hooks.register("url_hook")
def register_urls():
    """Register app urls"""

    return UrlHook(urls, "skillfarm", r"^skillfarm/")


@hooks.register("charlink")
def register_charlink_hook():
    return "skillfarm.thirdparty.charlink_hook"
