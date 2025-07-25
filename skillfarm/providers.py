"""Shared ESI client for Skillfarm."""

# Alliance Auth
from esi.clients import EsiClientProvider

# AA Skillfarm
from skillfarm import __app_name_useragent__, __github_url__, __title__, __version__

esi = EsiClientProvider(
    ua_appname=__app_name_useragent__, ua_version=__version__, ua_url=__github_url__
)
