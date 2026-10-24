"""Model for Permission."""

# Standard Library
from dataclasses import dataclass
from typing import Any, NamedTuple

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import User
from allianceauth.services.hooks import get_extension_logger

# AA Skillfarm
from skillfarm import __title__
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


class General(models.Model):
    """General model for app permissions and permission helpers."""

    class Permission(models.TextChoices):
        """All permissions of this app (codename, description)."""

        BASIC_ACCESS = "basic_access", _("Can access this app, Skillfarm.")
        CORP_ACCESS = (
            "corp_access",
            _("Has access to all characters in the corporation."),
        )
        ADMIN_ACCESS = "admin_access", _("Has access to all characters.")

    class Meta:
        managed = False
        default_permissions = ()
        verbose_name = "AA-Skillfarm"
        verbose_name_plural = "AA-Skillfarm"

    # Inject dynamic permissions
    Meta.permissions = Permission.choices

    @classmethod
    def get_perm(cls, perm: "str | General.Permission") -> str:
        """Return the full permission string 'skillfarm.<codename>'."""
        codename = perm.value if isinstance(perm, cls.Permission) else perm
        return f"skillfarm.{codename}"

    @classmethod
    def has_perm(cls, user: Any, perm: "str | General.Permission") -> bool:
        """Check if the user has the given permission."""
        if not user or not hasattr(user, "has_perm"):
            return False
        return user.has_perm(cls.get_perm(perm))

    @classmethod
    def has_any_perm(cls, user: Any, *perms: "str | General.Permission") -> bool:
        """Return True if the user has any of the given permissions."""
        if not user or not hasattr(user, "has_perm"):
            return False
        return any(user.has_perm(cls.get_perm(p)) for p in perms)


class UserSettings(models.Model):
    class Meta:
        default_permissions = ()

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="skillfarm_settings",
    )

    disable_notifications = models.BooleanField(default=False)


class UpdateSectionResult(NamedTuple):
    """A result of an attempted section update."""

    is_changed: bool | None
    is_updated: bool
    has_token_error: bool = False
    error_message: str | None = None
    data: Any = None


@dataclass(frozen=True)
class _NeedsUpdate:
    """An Object to track if an update is needed."""

    section_map: dict[str, bool]

    def __bool__(self) -> bool:
        """Check if any section needs an update."""
        return any(self.section_map.values())

    def for_section(self, section: str) -> bool:
        """Check if an update is needed for a specific section."""
        return self.section_map.get(section, False)
