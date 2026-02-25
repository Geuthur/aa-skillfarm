# Standard Library
from typing import TYPE_CHECKING

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Skillfarm
from skillfarm import __title__
from skillfarm.providers import AppLogger, esi

if TYPE_CHECKING:
    # pylint: disable=import-outside-toplevel
    # AA Skillfarm
    from skillfarm.models.prices import EveCategory, EveGroup, EveType

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


class EveTypeQuerySet(models.QuerySet):
    pass


class EveTypeManager(models.Manager["EveType"]):
    def get_queryset(self) -> EveTypeQuerySet:
        return EveTypeQuerySet(self.model, using=self._db)

    def get_or_create_from_esi(self, eve_id: int) -> "EveType":
        """Get or create an EveType by its ESI ID."""
        try:
            eve_type = self.get(type_id=eve_id)
            created = False
        except ObjectDoesNotExist:
            eve_type, created = self.update_or_create_from_esi(eve_id)
        return eve_type, created

    def update_or_create_from_esi(self, eve_id: int) -> "EveType":
        """Update or create an EveType by its ESI ID."""
        # AA Skillfarm
        # pylint: disable=import-outside-toplevel
        from skillfarm.models.prices import EveGroup

        try:
            response = esi._get_type(eve_id)
            group, created = EveGroup.objects.get_or_create_from_esi(response.group_id)
            eve_type, created = self.update_or_create(
                type_id=eve_id,
                defaults={
                    "name": response.name,
                    "eve_group": group,
                    "capacity": response.capacity,
                    "description": response.description,
                    "icon_id": response.icon_id,
                    "mass": response.mass,
                    "packaged_volume": response.packaged_volume,
                    "portion_size": response.portion_size,
                    "radius": response.radius,
                    "published": response.published,
                    "volume": response.volume,
                },
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("ESI Error for type ID %s: %s", eve_id, e)
            raise e
        return eve_type, created

    def bulk_get_or_create_esi(self, eve_ids: list[int]) -> list["EveType"]:
        """Bulk get or create EveTypes by their ESI IDs."""
        # AA Skillfarm
        # pylint: disable=import-outside-toplevel
        from skillfarm.models.prices import EveGroup

        _existing_types = self.filter(type_id__in=eve_ids)
        _existing_type_ids = set(_existing_types.values_list("type_id", flat=True))
        _current_groups_ids = set(
            EveGroup.objects.all().values_list("group_id", flat=True)
        )

        new_type_ids = [
            eve_id for eve_id in eve_ids if eve_id not in _existing_type_ids
        ]

        new_types = []
        for eve_id in new_type_ids:
            try:
                response = esi._get_type(eve_id)
                if response.group_id not in _current_groups_ids:
                    group = EveGroup.objects.get_or_create_from_esi(response.group_id)[
                        0
                    ]
                    # Add the new group ID to the current groups set to avoid redundant ESI calls
                    _current_groups_ids.add(response.group_id)
                else:
                    group = EveGroup.objects.get(group_id=response.group_id)
                new_types.append(
                    self.model(
                        name=response.name,
                        type_id=eve_id,
                        eve_group=group,
                        capacity=response.capacity,
                        description=response.description,
                        icon_id=response.icon_id,
                        mass=response.mass,
                        packaged_volume=response.packaged_volume,
                        portion_size=response.portion_size,
                        radius=response.radius,
                        published=response.published,
                        volume=response.volume,
                    )
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to get or create EveType for ID %s: %s", eve_id, e)

        if len(new_types) > 0:
            self.bulk_create(new_types, batch_size=500, ignore_conflicts=True)
        return list(_existing_types) + new_types


class EveGroupQuerySet(models.QuerySet):
    pass


class EveGroupManager(models.Manager["EveGroup"]):
    def get_queryset(self) -> EveGroupQuerySet:
        return EveGroupQuerySet(self.model, using=self._db)

    def get_or_create_from_esi(self, eve_id: int) -> "EveGroup":
        """Get or create an EveGroup by its ESI ID."""
        try:
            eve_group = self.get(group_id=eve_id)
            created = False
        except ObjectDoesNotExist:
            eve_group, created = self.update_or_create_from_esi(eve_id)
        return eve_group, created

    def update_or_create_from_esi(self, eve_id: int) -> "EveGroup":
        """Update or create an EveGroup by its ESI ID."""
        # AA Skillfarm
        # pylint: disable=import-outside-toplevel
        from skillfarm.models.prices import EveCategory

        try:
            response = esi._get_group(eve_id)
            category, created = EveCategory.objects.get_or_create_from_esi(
                response.category_id
            )
            eve_group, created = self.update_or_create(
                group_id=eve_id,
                defaults={
                    "name": response.name,
                    "eve_category": category,
                },
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("ESI Error for group ID %s: %s", eve_id, e)
            raise e
        return eve_group, created


class EveCategoryQuerySet(models.QuerySet):
    pass


class EveCategoryManager(models.Manager["EveCategory"]):
    def get_queryset(self) -> EveCategoryQuerySet:
        return EveCategoryQuerySet(self.model, using=self._db)

    def get_or_create_from_esi(self, eve_id: int) -> "EveCategory":
        """Get or create an EveCategory by its ESI ID."""
        try:
            eve_category = self.get(category_id=eve_id)
            created = False
        except ObjectDoesNotExist:
            eve_category, created = self.update_or_create_from_esi(eve_id)
        return eve_category, created

    def update_or_create_from_esi(self, eve_id: int) -> "EveCategory":
        """Update or create an EveCategory by its ESI ID."""
        try:
            response = esi._get_category(eve_id)
            eve_category, created = self.update_or_create(
                category_id=eve_id,
                defaults={
                    "name": response.name,
                },
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("ESI Error for category ID %s: %s", eve_id, e)
            raise e
        return eve_category, created
