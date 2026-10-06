# Standard Library
from typing import Generic, TypeVar

# Django
from django.db import models

# Alliance Auth
from allianceauth.authentication.models import User
from allianceauth.services.hooks import get_extension_logger

# AA Skillfarm
from skillfarm import __title__
from skillfarm.providers import AppLogger

logger = AppLogger(get_extension_logger(__name__), __title__)

T = TypeVar("T", bound=models.Model)


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
        # superusers get all visible
        if user.is_superuser:
            logger.debug(
                "Returning all objects for superuser %s.",
                user,
            )
            return self

        if user.has_perm("skillfarm.admin_access"):
            logger.debug("Returning all objects for admin user %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(character__character_ownership__user=user)]

            if user.has_perm("skillfarm.corp_access"):
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
        # superusers get all visible
        if user.is_superuser:
            logger.debug(
                "Returning all manageable queries for superuser %s.",
                user,
            )
            return self

        if user.has_perm("skillfarm.admin_access"):
            logger.debug("Returning all manageable queries for admin user %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(character__character_ownership__user=user)]

            if user.has_perm("skillfarm.corp_access"):
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
