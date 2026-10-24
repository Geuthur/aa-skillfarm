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

    @classmethod
    def has_basic_access(cls, user: Any) -> bool:
        """Check if the user may access the app (basic_access)."""
        return cls.has_perm(user, cls.Permission.BASIC_ACCESS)

    @classmethod
    def has_administration_access(cls, user: Any) -> bool:
        """Check if the user has system-wide administration access (admin_access)."""
        return cls.has_perm(user, cls.Permission.ADMIN_ACCESS)

    @classmethod
    def has_corporation_access(cls, user: Any) -> bool:
        """Check if the user has access to the own corporation (corp_access)."""
        return cls.has_perm(user, cls.Permission.CORP_ACCESS)

    @classmethod
    def has_management_access(cls, user: Any) -> bool:
        """Check if the user has any management permission (admin_access or corp_access)."""
        return cls.has_any_perm(
            user, cls.Permission.ADMIN_ACCESS, cls.Permission.CORP_ACCESS
        )

    @classmethod
    def is_superuser_only(cls, user: Any) -> bool:
        """Check if the user is a superuser (for superuser-only actions)."""
        return bool(user and getattr(user, "is_superuser", False))

    @classmethod
    def get_own_corporation_id(cls, user: Any) -> int | None:
        """Return the corporation ID of the main character of the user."""
        main_char = getattr(getattr(user, "profile", None), "main_character", None)
        return getattr(main_char, "corporation_id", None)

    @classmethod
    def get_corporation_scope(cls, user: Any) -> tuple[bool, bool, int | None]:
        """
        Resolve which corporations the user may see in the Administration.

        Returns:
            Tuple of (has_access, sees_all, own_corporation_id).
            `admin_access` sees all corporations, `corp_access` only the own one.
        """
        if not cls.has_basic_access(user):
            return False, False, None
        if cls.has_administration_access(user):
            return True, True, None
        if cls.has_corporation_access(user):
            return True, False, cls.get_own_corporation_id(user)
        return False, False, None


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
