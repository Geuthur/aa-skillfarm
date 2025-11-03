"""Shared ESI client for Skillfarm."""

# Alliance Auth
from esi.openapi_clients import ESIClientProvider

# AA Skillfarm
from skillfarm import (
    __app_name_useragent__,
    __characters_operations__,
    __esi_compatibility_date__,
    __github_url__,
    __title__,
    __version__,
)

esi = ESIClientProvider(
    compatibility_date=__esi_compatibility_date__,
    ua_appname=__app_name_useragent__,
    ua_version=__version__,
    ua_url=__github_url__,
    operations=__characters_operations__,
)
