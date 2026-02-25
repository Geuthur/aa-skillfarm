"""Model for Prices."""

# Django
from django.db import models

# AA Skillfarm
from skillfarm import __title__
from skillfarm.managers.eveonline import (
    EveCategoryManager,
    EveGroupManager,
    EveTypeManager,
)


class EveCategory(models.Model):
    """
    Eve Online Category Model.

    This model represents a category in the Eve Online universe. It is used to categorize groups and types of items.

    Args:
        category_id (int): The unique identifier for the category.
        name (str): The name of the category.
    """

    objects: EveCategoryManager = EveCategoryManager()
    category_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)


class EveGroup(models.Model):
    """
    Eve Online Group Model.

    This model represents a group in the Eve Online universe. It is used to group types of items together and is related to a category.

    Args:
    group_id (int): The unique identifier for the group.
    name (str): The name of the group.
    eve_category (EveCategory): The category to which this group belongs.
    """

    objects: EveGroupManager = EveGroupManager()

    class Meta:
        default_permissions = ()

    group_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    eve_category = models.ForeignKey(
        EveCategory, on_delete=models.SET_NULL, null=True, default=None
    )


class EveType(models.Model):
    """
    Eve Online Type Model.

    This model represents a type in the Eve Online universe. It contains detailed information about a specific type of item, including its attributes and relationships to groups and categories.

    Args:
    type_id (int): The unique identifier for the type.
    capacity (float): The capacity of the item.
    description (str): A description of the item.
    eve_group (EveGroup): The group to which this type belongs.
    icon_id (int): The ID of the icon representing this type.
    mass (float): The mass of the item
    packaged_volume (float): The volume of the item when packaged.
    portion_size (int): The portion size of the item.
    radius (float): The radius of the item.
    published (bool): Whether the item is published in the Eve Online universe.
    volume (float): The volume of the item.
    """

    objects: EveTypeManager = EveTypeManager()

    class Meta:
        default_permissions = ()

    type_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    eve_group = models.ForeignKey(
        EveGroup,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
    )
    capacity = models.FloatField(default=None, null=True)
    description = models.TextField(default="")
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    mass = models.FloatField(default=None, null=True)
    packaged_volume = models.FloatField(default=None, null=True)
    portion_size = models.PositiveIntegerField(default=None, null=True)
    radius = models.FloatField(default=None, null=True)
    published = models.BooleanField()
    volume = models.FloatField(default=None, null=True)


class EveTypePrice(models.Model):
    class Meta:
        default_permissions = ()

    name = models.CharField(
        max_length=255,
    )
    eve_type = models.OneToOneField(
        EveType,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    buy = models.DecimalField(max_digits=20, decimal_places=2)
    sell = models.DecimalField(max_digits=20, decimal_places=2)
    updated_at = models.DateTimeField()
