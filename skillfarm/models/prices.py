"""Model for Prices."""

# Django
from django.db import models

# Alliance Auth (External Libs)
from eve_sde.models.types import ItemType as EveType

# AA Skillfarm
from skillfarm import __title__


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
