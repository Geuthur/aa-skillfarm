"""App URLs"""

# Django
from django.urls import path, re_path

# AA Skillfarm
from skillfarm import views
from skillfarm.api import api

app_name: str = "skillfarm"  # pylint: disable=invalid-name

urlpatterns = [
    # -- API System
    re_path(r"^api/", api.urls),
    # -- ESI Character Addition
    path("char/add/", views.add_char, name="add_char"),
    # -- React SPA Routes
    re_path(
        r"^(?!api/|char/add).*$",
        views.react_base,
        name="react_base",
    ),
]
