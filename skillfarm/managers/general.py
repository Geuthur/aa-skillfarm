# Standard Library
from typing import Generic, TypeVar

# Django
from django.db import models

# Alliance Auth
from allianceauth.authentication.models import User

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
        """Users with `corp_access` see and manage their own corporation."""
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

    Methods:
        owned_by(user): Returns objects of characters owned by the given user.
        visible_to(user): Returns objects visible to the given user.
        manage_to(user): Returns objects the given user can manage.
    """

    def owned_by(self, user: User):
        """Get all objects of characters owned by the user, regardless of permissions."""
        return self.filter(character__character_ownership__user=user)

    def visible_to(self, user: User):
        """Get all objects visible to the user."""
        if GeneralManager.has_admin_access(user):
            logger.debug("Returning all objects for admin user %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(character__character_ownership__user=user)]

            if GeneralManager.has_corporation_access(user):
                queries.append(models.Q(character__corporation_id=char.corporation_id))

            logger.debug("%s queries for user %s visible.", len(queries), user)

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def manage_to(self, user: User):
        """Get QuerySet of objects that the user can manage."""
        if GeneralManager.has_admin_access(user):
            logger.debug("Returning all manageable queries for admin user %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(character__character_ownership__user=user)]

            if GeneralManager.has_corporation_access(user):
                queries.append(models.Q(character__corporation_id=char.corporation_id))

            logger.debug("%s queries for user %s manageable.", len(queries), user)

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing manageable.", user)
            return self.none()


class AccessManager(models.Manager[T], Generic[T]):
    """
    A Manager with access control methods for the whole Application

    This manager provides methods to filter querysets based on user permissions,
    such as `visible_to` and `manage_to`, ensuring that users only see or manage
    the objects they are allowed to.
    """

    def get_queryset(self) -> AccessQuerySet[T]:
        return AccessQuerySet(self.model, using=self._db)

    def owned_by(self, user: User):
        return self.get_queryset().owned_by(user)

    def visible_to(self, user: User):
        return self.get_queryset().visible_to(user)

    def manage_to(self, user: User):
        return self.get_queryset().manage_to(user)
