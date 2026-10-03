# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Skillfarm
from skillfarm import __title__
from skillfarm.managers.general import AccessManager, AccessQuerySet
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)

if TYPE_CHECKING:
    # AA Skillfarm
    from skillfarm.models.skillfarmaudit import SkillFarmAudit as SkillFarmAuditType


class SkillfarmQuerySet(AccessQuerySet["SkillFarmAuditType"]):
    def training_active(self):
        """Return characters with active training."""
        return self.filter(is_training=True)

    def training_paused(self):
        """Return characters with paused or empty training queues."""
        return self.filter(is_training=False)

    def extractions_pending(self):
        """Return characters with ready extractions that have not yet been acknowledged."""
        return self.filter(extractions_ready_count__gt=0, extraction_acknowledged=False)

    def extractions_acknowledged(self):
        """Return characters with ready extractions that have been acknowledged."""
        return self.filter(extractions_ready_count__gt=0, extraction_acknowledged=True)

    def filter_by_schema(self, filters) -> "SkillfarmQuerySet":
        """Filter queryset by CharacterFilter schema."""
        qs = self

        search = getattr(filters, "search", None)
        if search:
            search_term = str(search).strip()
            qs = qs.filter(
                models.Q(character__character_name__icontains=search_term)
                | models.Q(character__corporation_name__icontains=search_term)
                | models.Q(character__corporation_ticker__icontains=search_term)
            )

        corp_id = getattr(filters, "corporation_id", None)
        if corp_id:
            qs = qs.filter(character__corporation_id=corp_id)

        training_status = getattr(filters, "training_status", "all")
        if training_status == "training":
            qs = qs.filter(is_training=True)
        elif training_status == "paused":
            qs = qs.filter(is_training=False)

        extraction_status = getattr(filters, "extraction_status", "all")
        if extraction_status == "pending":
            qs = qs.filter(extractions_ready_count__gt=0, extraction_acknowledged=False)
        elif extraction_status == "acknowledged":
            qs = qs.filter(extractions_ready_count__gt=0, extraction_acknowledged=True)
        elif extraction_status == "none":
            qs = qs.filter(extractions_ready_count=0)

        notification_status = getattr(filters, "notification_status", "all")
        if notification_status == "enabled":
            qs = qs.filter(notification=True)
        elif notification_status == "disabled":
            qs = qs.filter(notification=False)

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


class SkillFarmManager(AccessManager["SkillFarmAuditType"]):
    def get_queryset(self):
        return SkillfarmQuerySet(self.model, using=self._db)

    def training_active(self):
        """Return characters with active training."""
        return self.get_queryset().training_active()

    def training_paused(self):
        """Return characters with paused or empty training queues."""
        return self.get_queryset().training_paused()

    def extractions_pending(self):
        """Return characters with ready extractions that have not yet been acknowledged."""
        return self.get_queryset().extractions_pending()

    def extractions_acknowledged(self):
        """Return characters with ready extractions that have been acknowledged."""
        return self.get_queryset().extractions_acknowledged()

    def filter_by_schema(self, filters):
        """Filter characters by CharacterFilter schema."""
        return self.get_queryset().filter_by_schema(filters)

    def disable_characters_with_no_owner(self) -> int:
        """Disable characters which have no owner. Return count of disabled characters."""
        return self.get_queryset().disable_characters_with_no_owner()
