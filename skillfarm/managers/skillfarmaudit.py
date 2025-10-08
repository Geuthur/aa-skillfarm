# Django
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import models
from django.db.models import Case, Count, Q, Value, When
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Skillfarm
from skillfarm import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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

    def annotate_total_update_status_user(self, user):
        """Get the total update status for the given user."""
        char = user.profile.main_character
        assert char

        query = models.Q(character__character_ownership__user=user)

        return self.filter(query).annotate_total_update_status()

    def annotate_total_update_status(self):
        """Get the total update status."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        # AA Skillfarm
        from skillfarm.models.skillfarmaudit import SkillFarmAudit

        sections = SkillFarmAudit.UpdateSection.get_sections()
        num_sections_total = len(sections)
        qs = (
            self.annotate(
                num_sections_total=Count(
                    "skillfarm_update_status",
                    filter=Q(skillfarm_update_status__section__in=sections),
                )
            )
            .annotate(
                num_sections_ok=Count(
                    "skillfarm_update_status",
                    filter=Q(
                        skillfarm_update_status__section__in=sections,
                        skillfarm_update_status__is_success=True,
                    ),
                )
            )
            .annotate(
                num_sections_failed=Count(
                    "skillfarm_update_status",
                    filter=Q(
                        skillfarm_update_status__section__in=sections,
                        skillfarm_update_status__is_success=False,
                    ),
                )
            )
            .annotate(
                num_sections_token_error=Count(
                    "skillfarm_update_status",
                    filter=Q(
                        skillfarm_update_status__section__in=sections,
                        skillfarm_update_status__has_token_error=True,
                    ),
                )
            )
            # pylint: disable=no-member
            .annotate(
                total_update_status=Case(
                    When(
                        active=False,
                        then=Value(SkillFarmAudit.UpdateStatus.DISABLED),
                    ),
                    When(
                        num_sections_token_error=1,
                        then=Value(SkillFarmAudit.UpdateStatus.TOKEN_ERROR),
                    ),
                    When(
                        num_sections_failed__gt=0,
                        then=Value(SkillFarmAudit.UpdateStatus.ERROR),
                    ),
                    When(
                        num_sections_ok=num_sections_total,
                        then=Value(SkillFarmAudit.UpdateStatus.OK),
                    ),
                    When(
                        num_sections_total__lt=num_sections_total,
                        then=Value(SkillFarmAudit.UpdateStatus.INCOMPLETE),
                    ),
                    default=Value(SkillFarmAudit.UpdateStatus.IN_PROGRESS),
                )
            )
        )

        return qs

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

    def last_update_status(self, character):
        """Return the last update status for the given character."""
        # Filter update status
        update_status = (
            character.skillfarm_update_status.order_by("last_update_finished_at")
            .exclude(last_update_finished_at__isnull=True)
            .first()
        )

        if update_status:
            last_update_display = naturaltime(update_status.last_update_finished_at)
        else:
            last_update_display = character.get_status.description()
        return last_update_display


class SkillFarmManagerBase(models.Manager):
    def get_queryset(self):
        return SkillfarmQuerySet(self.model, using=self._db)

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

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)


SkillFarmManager = SkillFarmManagerBase.from_queryset(SkillfarmQuerySet)
