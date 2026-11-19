"""App URLs"""

# Django
from django.urls import path, re_path

# Alliance Auth
from allianceauth.authentication.decorators import decorate_url_patterns

# AA Skillfarm
from skillfarm import views
from skillfarm.api import api
from skillfarm.api.auth import basic_access_required

app_name: str = "skillfarm"  # pylint: disable=invalid-name

# Every URL of the API (endpoints, schema and docs) requires `basic_access`
api_patterns, api_app_name, api_namespace = api.urls
api_patterns = decorate_url_patterns(
    (api_patterns, api_app_name), basic_access_required
)[0]

urlpatterns = [
    # -- API System
    re_path(r"^api/", (api_patterns, api_app_name, api_namespace)),
    # -- ESI Character Addition
    path("char/add/", views.add_char, name="add_char"),
    # -- React SPA Routes
    re_path(
        r"^(?!api/|char/add).*$",
        views.react_base,
        name="react_base",
    ),
]
