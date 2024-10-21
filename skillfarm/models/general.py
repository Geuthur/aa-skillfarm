"""Model for Permission."""

from django.db import models

from skillfarm.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class General(models.Model):
    """General model for app permissions"""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app, Skillfarm."),
            ("corp_access", "Has access to all characters in the corporation."),
            ("admin_access", "Has access to all characters."),
        )
