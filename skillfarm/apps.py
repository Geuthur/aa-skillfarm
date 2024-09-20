"""App Configuration"""

# Django
from django.apps import AppConfig

# AA Example App
from skillfarm import __version__


class SkillfarmConfig(AppConfig):
    """App Config"""

    default_auto_field = "django.db.models.AutoField"
    author = "Geuthur"
    name = "skillfarm"
    label = "skillfarm"
    verbose_name = f"Skillfarm v{__version__}"
