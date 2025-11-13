# Third Party
from ninja import NinjaAPI
from ninja.security import django_auth

# Django
from django.conf import settings

# AA Skillfarm
from skillfarm.api import skillfarm

api = NinjaAPI(
    title="AA Skillfarm API",
    version="0.5.0",
    urls_namespace="skillfarm:api",
    auth=django_auth,
    openapi_url=settings.DEBUG and "/openapi.json" or "",
)


def setup(ninja_api):
    skillfarm.SkillFarmApiEndpoints(ninja_api)


# Initialize API endpoints
setup(api)
