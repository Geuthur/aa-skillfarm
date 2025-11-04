"""App URLs"""

# Django
from django.urls import path, re_path

# AA Skillfarm
from skillfarm import views
from skillfarm.api import api

app_name: str = "skillfarm"  # pylint: disable=invalid-name

urlpatterns = [
    # -- Views
    path("", views.index, name="index"),
    path("admin/", views.admin, name="admin"),
    path(
        "<int:character_id>/view/skillfarm/",
        views.skillfarm,
        name="skillfarm",
    ),
    path(
        "view/overview/",
        views.character_overview,
        name="character_overview",
    ),
    # -- Administration
    path("char/add/", views.add_char, name="add_char"),
    path(
        "switch_alarm/<int:character_id>/",
        views.switch_alarm,
        name="switch_alarm",
    ),
    path(
        "delete/<int:character_id>/",
        views.delete_character,
        name="delete_character",
    ),
    path(
        "skillset/<int:character_id>/",
        views.skillset,
        name="skillset",
    ),
    # -- Tools
    path("calc/", views.skillfarm_calc, name="calc"),
    # -- API System
    re_path(r"^api/", api.urls),
]
