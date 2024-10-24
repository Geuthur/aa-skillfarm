"""Models for Skillfarm."""

from django.db import models

from skillfarm.hooks import get_extension_logger
from skillfarm.managers.skillfarmaudit import SkillFarmManager

logger = get_extension_logger(__name__)


class SkillFarmSetup(models.Model):
    id = models.AutoField(primary_key=True)

    character = models.OneToOneField(
        "SkillFarmAudit", on_delete=models.CASCADE, related_name="skillfarm_setup"
    )

    skillset = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.skillset}'s Skill Setup"

    objects = SkillFarmManager()

    class Meta:
        default_permissions = ()
