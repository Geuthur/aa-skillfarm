"""Model for Prices."""

# Django
from django.db import models

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveType

# AA Skillfarm
from skillfarm import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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
