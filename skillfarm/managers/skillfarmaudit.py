# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

# AA Skillfarm
from skillfarm import __title__
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)

if TYPE_CHECKING:
    # AA Skillfarm
    from skillfarm.models.skillfarmaudit import SkillFarmAudit as SkillFarmAuditType


class SkillfarmQuerySet(models.QuerySet):
    def visible_to(self, user):
        # superusers get all visible
        if user.is_superuser:
            logger.debug("Returning all characters for superuser %s.", user)
            return self

        if user.has_perm("skillfarm.admin_access"):
            logger.debug("Returning all characters for admin %s.", user)
            return self

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(character__character_ownership__user=user)]

            if user.has_perm("skillfarm.corp_access"):
                queries.append(models.Q(character__corporation_id=char.corporation_id))

            logger.debug(
                "%s queries for user %s visible chracters.", len(queries), user
            )

            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return self.none()

    def disable_characters_with_no_owner(self) -> int:
        """Disable characters which have no owner. Return count of disabled characters."""
        orphaned_characters = self.filter(
            character__character_ownership__isnull=True, active=True
        )
        if orphaned_characters.exists():
            orphans = list(
                orphaned_characters.values_list(
                    "character__character_name", flat=True
                ).order_by("character__character_name")
            )
            orphaned_characters.update(active=False)
            logger.info(
                "Disabled %d characters which do not belong to a user: %s",
                len(orphans),
                ", ".join(orphans),
            )
            return len(orphans)
        return 0


class SkillFarmManager(models.Manager["SkillFarmAuditType"]):
    def get_queryset(self):
        return SkillfarmQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        """Return characters visible to the given user."""
        return self.get_queryset().visible_to(user)

    def disable_characters_with_no_owner(self) -> int:
        """Disable characters which have no owner. Return count of disabled characters."""
        return self.get_queryset().disable_characters_with_no_owner()

    @staticmethod
    def visible_eve_characters(user):
        qs = EveCharacter.objects.get_queryset()
        if user.is_superuser:
            logger.debug("Returning all characters for superuser %s.", user)
            return qs.all()

        if user.has_perm("skillfarm.admin_access"):
            logger.debug("Returning all characters for admin %s.", user)
            return qs.all()

        try:
            char = user.profile.main_character
            assert char
            queries = [models.Q(character_ownership__user=user)]

            if user.has_perm("skillfarm.corp_access"):
                queries.append(models.Q(corporation_id=char.corporation_id))

            logger.debug(
                "%s queries for user %s visible chracters.", len(queries), user
            )

            query = queries.pop()
            for q in queries:
                query |= q
            return qs.filter(query)
        except AssertionError:
            logger.debug("User %s has no main character. Nothing visible.", user)
            return qs.none()
