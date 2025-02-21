"""App URLs"""

from django.urls import path, re_path

from skillfarm import views
from skillfarm.api import api

app_name: str = "skillfarm"

urlpatterns = [
    # -- Views
    path("", views.index, name="index"),
    path(
        "<int:character_id>/view/skillfarm/",
        views.skillfarm,
        name="skillfarm",
    ),
    path(
        "<int:character_id>/view/overview/",
        views.character_overview,
        name="character_overview",
    ),
    # -- Administration
    path("char/add/", views.add_char, name="add_char"),
    path(
        "char/delete/<int:character_id>/",
        views.remove_char,
        name="remove_char",
    ),
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
    # -- Tools
    path("calc/", views.skillfarm_calc, name="calc"),
    # -- API System
    re_path(r"^api/", api.urls),
]
