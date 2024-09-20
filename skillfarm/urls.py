"""App URLs"""

from django.urls import path, re_path

from skillfarm import views
from skillfarm.api import api

app_name: str = "skillfarm"

urlpatterns = [
    path("", views.index, name="index"),
    path("char/add/", views.add_char, name="add_char"),
    path(
        "<int:character_pk>/",
        views.skillfarm,
        name="skillfarm",
    ),
    path(
        "<int:character_pk>/filter/",
        views.skillfarmfilter,
        name="skillfarmfilter",
    ),
    path("character_admin/", views.character_admin, name="character_admin"),
    path(
        "switch_alarm/<int:character_id>/",
        views.switch_alarm,
        name="switch_alarm",
    ),
    path(
        "skillset/<int:character_id>/",
        views.skillset,
        name="skillset",
    ),
    # -- API System
    re_path(r"^api/", api.urls),
]
