"""Model for Prices."""

from django.db import models
from eveuniverse.models import EveType

from skillfarm.hooks import get_extension_logger

logger = get_extension_logger(__name__)


class EveTypePrice(models.Model):
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    eve_type = models.OneToOneField(
        EveType,
        on_delete=models.deletion.CASCADE,
        primary_key=True,
    )
    buy = models.DecimalField(max_digits=20, decimal_places=2)
    sell = models.DecimalField(max_digits=20, decimal_places=2)
    updated_at = models.DateTimeField()
