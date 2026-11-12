"""Model for Permission."""

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import User

# AA Skillfarm
from skillfarm.managers.general import GeneralManager


class General(models.Model):
    """A model defining the permissions of Skillfarm.

    Permissions are checked with Django and the full string, e.g.
    `@permission_required("skillfarm.basic_access")` or
    `user.has_perm("skillfarm.basic_access")`.
    """

    objects = GeneralManager()

    class Meta:
        managed = False
        default_permissions = ()
        verbose_name = "AA-Skillfarm"
        verbose_name_plural = "AA-Skillfarm"
        permissions = (
            ("basic_access", _("Can access this app, Skillfarm.")),
            (
                "corp_access",
                _("Has access to all characters in the corporation."),
            ),
            ("admin_access", _("Has access to all characters.")),
        )


class UserSettings(models.Model):
    class Meta:
        default_permissions = ()

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="skillfarm_settings",
    )

    disable_notifications = models.BooleanField(default=False)
