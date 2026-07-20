# Standard Library
from typing import TYPE_CHECKING

# Django
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import models
from django.db.models import Case, Count, Q, Value, When
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Skillfarm
from skillfarm import __title__
from skillfarm.models.helpers.update_manager import CharacterUpdateSection, UpdateStatus
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)

if TYPE_CHECKING:
    # AA Skillfarm
    from skillfarm.models.skillfarmaudit import (
        CharacterUpdateStatus as CharacterUpdateStatusType,
    )


class UpdateStatusQuerySet(models.QuerySet["CharacterUpdateStatusType"]):
    def last_update_status(self) -> str:
        """Return the last update status."""
        # Filter update status
        update_status = (
            self.order_by("last_update_finished_at")
            .exclude(last_update_finished_at__isnull=True)
            .first()
        )

        if update_status:
            last_update_display = naturaltime(update_status.last_update_finished_at)
            return last_update_display
        return UpdateStatus.description(UpdateStatus.INCOMPLETE)

    def get_status(self) -> UpdateStatus:
        """Return the current aggregate update status."""
        total_update_status = (
            self.annotate_total_update_status()
            .values_list("total_update_status", flat=True)
            .order_by("total_update_status")
            .first()
        )

        if total_update_status is None:
            return UpdateStatus.INCOMPLETE
        return UpdateStatus(total_update_status)

    def annotate_total_update_status(self):
        """Get the total update status."""
        sections = CharacterUpdateSection.get_sections()
        total_sections = len(sections)
        qs = (
            self.values("character_id", "character__active")
            .annotate(
                num_sections_found=Count(
                    "pk",
                    filter=Q(section__in=sections),
                )
            )
            .annotate(
                num_sections_ok=Count(
                    "pk",
                    filter=Q(
                        section__in=sections,
                        is_success=True,
                    ),
                )
            )
            .annotate(
                num_sections_failed=Count(
                    "pk",
                    filter=Q(
                        section__in=sections,
                        is_success=False,
                    ),
                )
            )
            .annotate(
                num_sections_token_error=Count(
                    "pk",
                    filter=Q(
                        section__in=sections,
                        has_token_error=True,
                    ),
                )
            )
            # pylint: disable=no-member
            .annotate(
                total_update_status=Case(
                    When(
                        character__active=False,
                        then=Value(UpdateStatus.DISABLED),
                    ),
                    When(
                        num_sections_token_error__gt=0,
                        then=Value(UpdateStatus.TOKEN_ERROR),
                    ),
                    When(
                        num_sections_failed__gt=0,
                        then=Value(UpdateStatus.ERROR),
                    ),
                    When(
                        num_sections_ok=total_sections,
                        then=Value(UpdateStatus.OK),
                    ),
                    When(
                        num_sections_found__lt=total_sections,
                        then=Value(UpdateStatus.INCOMPLETE),
                    ),
                    default=Value(UpdateStatus.IN_PROGRESS),
                )
            )
        )

        return qs


class UpdateStatusManager(models.Manager["CharacterUpdateStatusType"]):
    def get_queryset(self):
        return UpdateStatusQuerySet(model=self.model, using=self._db)

    def last_update_status(self) -> str:
        return self.get_queryset().last_update_status()

    def get_status(self) -> UpdateStatus:
        """Return the last update status for the given character."""
        return self.get_queryset().get_status()

    def annotate_total_update_status(
        self,
    ) -> models.QuerySet["CharacterUpdateStatusType"]:
        """Return the total update status."""
        return self.get_queryset().annotate_total_update_status()
