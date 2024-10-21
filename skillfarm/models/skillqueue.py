"""Models for Skillfarn Queue."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from eveuniverse.models import EveType

from skillfarm.hooks import get_extension_logger
from skillfarm.managers.skillqueue import SkillqueueManager

logger = get_extension_logger(__name__)


class CharacterSkillqueueEntry(models.Model):
    """Skillfarm Skillqueue model for app"""

    character = models.ForeignKey(
        "SkillFarmAudit",
        on_delete=models.CASCADE,
        related_name="skillqueue",
    )
    queue_position = models.PositiveIntegerField(db_index=True)

    finish_date = models.DateTimeField(default=None, null=True)
    finished_level = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    level_end_sp = models.PositiveIntegerField(default=None, null=True)
    level_start_sp = models.PositiveIntegerField(default=None, null=True)
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    start_date = models.DateTimeField(default=None, null=True)
    training_start_sp = models.PositiveIntegerField(default=None, null=True)

    objects = SkillqueueManager()

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.character}-{self.queue_position}"

    @property
    def is_active(self) -> bool:
        """Returns true when this skill is currently being trained"""
        return bool(self.finish_date) and self.queue_position == 0