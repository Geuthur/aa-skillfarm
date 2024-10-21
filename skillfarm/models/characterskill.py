"""Model for CharacterSkill."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from eveuniverse.models import EveType

from skillfarm.hooks import get_extension_logger
from skillfarm.managers.characterskill import CharacterSkillManager

logger = get_extension_logger(__name__)


class CharacterSkill(models.Model):
    """Skillfarm Character Skill model for app"""

    character = models.ForeignKey(
        "SkillFarmAudit", on_delete=models.CASCADE, related_name="character_skills"
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")

    active_skill_level = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    skillpoints_in_skill = models.PositiveBigIntegerField()
    trained_skill_level = models.PositiveBigIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    objects = CharacterSkillManager()

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.character}-{self.eve_type.name}"
