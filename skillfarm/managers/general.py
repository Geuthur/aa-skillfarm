"""Access control for the app: querysets and managers with `visible_to` and `manage_to`."""

# Standard Library
from typing import Generic, TypeVar

# Django
from django.db import models

# AA Skillfarm
from skillfarm.providers import logger

T = TypeVar("T", bound=models.Model)


class GeneralManager(models.Manager):
    """
    Manager of `General` for the app's own permission rules.

    Django checks single permissions (`user.has_perm("skillfarm.basic_access")`).
    This manager only holds the rules that combine them. `General` is not
    managed, so these methods never query the database.
    """

    @staticmethod
    def has_basic_access(user) -> bool:
        """Users with `basic_access` may use the app."""
        return bool(user.has_perm("skillfarm.basic_access"))

    @staticmethod
    def has_admin_access(user) -> bool:
        """Users with `admin_access` see and manage everything."""
        return bool(user.has_perm("skillfarm.admin_access"))

    @staticmethod
    def has_corporation_access(user) -> bool:
        """Users with `corp_access` see their own corporation. They manage only their own characters."""
        return bool(user.has_perm("skillfarm.corp_access"))

    @staticmethod
    def has_superuser_access(user) -> bool:
        """Superusers only (global tasks, deleting audits)."""
        return bool(user.is_superuser)

    @staticmethod
    def has_management_access(user) -> bool:
        """Users with `admin_access` or `corp_access` may use the Administration."""
        return bool(
            GeneralManager.has_admin_access(user)
            or GeneralManager.has_corporation_access(user)
        )

    @staticmethod
    def get_corporation_scope(user) -> tuple[bool, bool, int | None]:
        """
        Resolve which corporations the user may see in the Administration.

        Returns:
            Tuple of (has_access, sees_all, own_corporation_id).
            `admin_access` sees all corporations, `corp_access` only the own one.
        """
        if not GeneralManager.has_basic_access(user):
            return False, False, None
        if GeneralManager.has_admin_access(user):
            return True, True, None
        if GeneralManager.has_corporation_access(user):
            main_char = getattr(getattr(user, "profile", None), "main_character", None)
            return True, False, getattr(main_char, "corporation_id", None)
        return False, False, None


class AccessQuerySet(models.QuerySet[T], Generic[T]):
    """
    A QuerySet with access control methods for the whole Application.

    Same shape as the app template (aa-example). The rules assume a
    `character` foreign key to `EveCharacter`: a user sees and manages the
    objects of their own characters. Override `visible_q` and `manage_q` in a
    subclass when a model needs other rules.

    Deviations from the template, because the rules of this app differ:

    - `sees_all` and `manages_all` replace the `has_full_access` check: who has
      `admin_access` gets everything. There is no own superuser branch.
    - `corp_access` adds the characters of the own corporation (the
      corporation of the main character) to `visible_q` only. It never widens
      `manage_q`: without `admin_access` a user manages the own characters.
    - `_restricted_to` takes the Q method instead of the Q object and calls it
      only after the main character check: the rule for `corp_access` reads
      the main character, which a user without one does not have.
    - `owned_by` exists as a method: the API lists the own characters with it,
      regardless of permissions and main character.

    Methods:
        owned_by(user): Returns objects of characters owned by the given user.
        visible_to(user): Returns objects visible to the given user.
        manage_to(user): Returns objects the given user can manage.
    """

    def sees_all(self, user) -> bool:
        """Whether the user sees every object without a filter."""
        return GeneralManager.has_admin_access(user)

    def manages_all(self, user) -> bool:
        """Whether the user manages every object without a filter."""
        return GeneralManager.has_admin_access(user)

    def owned_by_q(self, user) -> models.Q:
        """Q object for the objects that belong to the user's characters."""
        return models.Q(character__character_ownership__user=user)

    def corporation_q(self, user) -> models.Q:
        """Q object for the objects of the user's own corporation (needs a main character)."""
        return models.Q(
            character__corporation_id=user.profile.main_character.corporation_id
        )

    def visible_q(self, user) -> models.Q:
        """Q object for the objects a user who does not see all may see."""
        query = self.owned_by_q(user)
        if GeneralManager.has_corporation_access(user):
            query |= self.corporation_q(user)
        return query

    def manage_q(self, user) -> models.Q:
        """Q object for the objects a user who does not manage all may manage."""
        return self.owned_by_q(user)

    def _restricted_to(self, user, has_all: bool, query, what: str):
        if has_all:
            logger.debug("Returning all %s objects for %s.", what, user)
            return self

        if not getattr(user.profile, "main_character", None):
            logger.debug("User %s has no main character. Nothing %s.", user, what)
            return self.none()

        return self.filter(query(user))

    def owned_by(self, user):
        """Get all objects of characters owned by the user, regardless of permissions."""
        return self.filter(self.owned_by_q(user))

    def visible_to(self, user):
        """Get all objects visible to the user."""
        return self._restricted_to(user, self.sees_all(user), self.visible_q, "visible")

    def manage_to(self, user):
        """Get QuerySet of objects that the user can manage."""
        return self._restricted_to(
            user, self.manages_all(user), self.manage_q, "manageable"
        )


class AccessManager(models.Manager[T], Generic[T]):
    """
    A Manager with access control methods for the whole Application

    This manager provides methods to filter querysets based on user permissions,
    such as `visible_to` and `manage_to`, ensuring that users only see or manage
    the objects they are allowed to.
    """

    def get_queryset(self) -> AccessQuerySet[T]:
        return AccessQuerySet(self.model, using=self._db)

    def owned_by(self, user):
        return self.get_queryset().owned_by(user)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user):
        return self.get_queryset().manage_to(user)
