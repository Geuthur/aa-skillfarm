"""App URLs"""

from django.urls import path, re_path

from skillfarm import views
from skillfarm.api import api

app_name: str = "skillfarm"

urlpatterns = [
    path("", views.index, name="index"),
    path("char/add/", views.add_char, name="add_char"),
    path(
        "char/delete/<int:character_id>/",
        views.remove_char,
        name="remove_char",
    ),
    path(
        "<int:character_pk>/",
        views.skillfarm,
        name="skillfarm",
    ),
    path("character_admin/", views.character_admin, name="character_admin"),
    path(
        "switch_alarm/<int:character_id>/",
        views.switch_alarm,
        name="switch_alarm",
    ),
    path(
        "switch_activity/<int:character_id>/",
        views.switch_activity,
        name="switch_activity",
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
