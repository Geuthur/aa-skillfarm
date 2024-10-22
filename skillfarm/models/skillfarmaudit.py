"""Models for Skillfarm."""

import datetime

from django.db import models
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter, Token

from skillfarm import app_settings
from skillfarm.hooks import get_extension_logger
from skillfarm.managers.skillfarmaudit import SkillFarmManager

logger = get_extension_logger(__name__)


class SkillFarmAudit(models.Model):
    """Character Audit model for app"""

    id = models.AutoField(primary_key=True)

    active = models.BooleanField(default=True)

    character = models.OneToOneField(
        EveCharacter, on_delete=models.CASCADE, related_name="skillfarm_character"
    )

    notification = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False)
    last_notification = models.DateTimeField(null=True, default=None, blank=True)

    last_update_skills = models.DateTimeField(null=True, default=None, blank=True)
    last_update_skillqueue = models.DateTimeField(null=True, default=None, blank=True)

    objects = SkillFarmManager()

    def __str__(self):
        return f"{self.character.character_name}'s Character Data"

    class Meta:
        default_permissions = ()

    @classmethod
    def get_esi_scopes(cls) -> list[str]:
        """Return list of required ESI scopes to fetch."""
        return [
            "esi-skills.read_skills.v1",
            "esi-skills.read_skillqueue.v1",
        ]

    def get_token(self) -> Token:
        """Helper method to get a valid token for a specific character with specific scopes."""
        token = (
            Token.objects.filter(character_id=self.character.character_id)
            .require_scopes(self.get_esi_scopes())
            .require_valid()
            .first()
        )
        if token:
            return token
        return False

    def finished_skills(self) -> list[str]:
        """Check if a character has a skill finished from filter."""
        # pylint: disable=import-outside-toplevel
        from skillfarm.models import CharacterSkill

        skill_names = []
        try:
            character = SkillFarmSetup.objects.get(character=self)
        except SkillFarmSetup.DoesNotExist:
            character = None

        if character and character.skillset is not None:
            skills = CharacterSkill.objects.filter(
                character=self,
                eve_type__name__in=character.skillset,
            )

            for skill in skills:
                if skill.trained_skill_level == 5:
                    skill_names.append(skill.eve_type.name)
        return skill_names

    @property
    def is_active(self):
        time_ref = timezone.now() - datetime.timedelta(
            days=app_settings.SKILLFARM_CHAR_MAX_INACTIVE_DAYS
        )
        try:
            is_active = True

            is_active = self.last_update_skillqueue > time_ref
            is_active = self.last_update_skills > time_ref

            if self.active != is_active:
                self.active = is_active
                self.save()

            return is_active
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    @property
    def is_cooldown(self) -> bool:
        """Check if a character has a notification cooldown."""
        if self.last_notification is None:
            return False

        if self.last_notification < timezone.now() - datetime.timedelta(
            days=app_settings.SKILLFARM_NOTIFICATION_COOLDOWN
        ):
            self.delete()
            return False
        return True


class SkillFarmSetup(models.Model):
    id = models.AutoField(primary_key=True)

    character = models.OneToOneField(
        SkillFarmAudit, on_delete=models.CASCADE, related_name="skillfarm_setup"
    )

    skillset = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.skillset}'s Skill Setup"

    objects = SkillFarmManager()

    class Meta:
        default_permissions = ()
