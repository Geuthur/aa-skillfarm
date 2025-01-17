"""Models for Skillfarm."""

import datetime

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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

    def skill_extraction(self) -> list[str]:
        """Check if a character has a skill extraction ready and return skill names."""
        # pylint: disable=import-outside-toplevel
        from skillfarm.models.characterskill import CharacterSkill
        from skillfarm.models.skillfarmsetup import SkillFarmSetup

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

    def skillqueue_extraction(self) -> list[str]:
        """Check if a character has a skillqueue Extraction ready and return skill names."""
        # pylint: disable=import-outside-toplevel
        from skillfarm.models.skillfarmsetup import SkillFarmSetup
        from skillfarm.models.skillqueue import CharacterSkillqueueEntry

        skill_names = []
        try:
            character = SkillFarmSetup.objects.get(character=self)
        except SkillFarmSetup.DoesNotExist:
            character = None

        if character and character.skillset is not None:
            skillqueue = CharacterSkillqueueEntry.objects.filter(character=self)

            for skill in skillqueue:
                if skill.is_skillqueue_ready:
                    skill_names.append(skill.eve_type.name)
        return skill_names

    def _generate_notification(self, skill_names: list[str]) -> str:
        """Generate notification for the user."""
        msg = _("%(charname)s: %(skillname)s") % {
            "charname": self.character.character_name,
            "skillname": ", ".join(skill_names),
        }
        return msg

    def get_finished_skills(self) -> list[str]:
        """Return a list of finished skills."""
        skill_names = set()
        skills = self.skill_extraction()
        skillqueue = self.skillqueue_extraction()

        if skillqueue:
            skill_names.update(skillqueue)
        if skills:
            skill_names.update(skills)

        return list(skill_names)

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
        return True
