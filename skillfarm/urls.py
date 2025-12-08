"""App URLs"""

# Django
from django.urls import path, re_path

# AA Skillfarm
from skillfarm import views
from skillfarm.api import api

app_name: str = "skillfarm"  # pylint: disable=invalid-name

urlpatterns = [
    # -- Views
    path("view/skillfarm/", views.index, name="index"),
    path(
        "<int:character_id>/view/skillfarm/",
        views.index,
        name="index",
    ),
    path("admin/", views.admin, name="admin"),
    path(
        "view/overview/",
        views.character_overview,
        name="character_overview",
    ),
    # -- Administration
    path("char/add/", views.add_char, name="add_char"),
    path(
        "switch_notification/<int:character_id>/",
        views.switch_notification,
        name="switch_notification",
    ),
    path(
        "delete_character/<int:character_id>/",
        views.delete_character,
        name="delete_character",
    ),
    path(
        "edit_skillsetup/<int:character_id>/",
        views.edit_skillsetup,
        name="edit_skillsetup",
    ),
    # -- Tools
    path("view/calculator/", views.skillfarm_calc, name="calculator"),
    # -- API System
    re_path(r"^api/", api.urls),
]
