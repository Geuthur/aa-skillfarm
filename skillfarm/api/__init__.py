"""AA Skillfarm Django Ninja API Initialization."""

# Third Party
from ninja import NinjaAPI
from ninja.security import django_auth

# Django
from django.conf import settings

# AA Skillfarm
from skillfarm.api import admin, calculator, characters, general, overview

api = NinjaAPI(
    title="AA Skillfarm API",
    version="1.0.0",
    urls_namespace="skillfarm:api",
    auth=django_auth,
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)


def setup(ninja_api: NinjaAPI):
    general.ApiEndpoints(ninja_api)
    characters.ApiEndpoints(ninja_api)
    calculator.ApiEndpoints(ninja_api)
    overview.ApiEndpoints(ninja_api)
    admin.ApiEndpoints(ninja_api)


# Initialize API endpoints
setup(api)
