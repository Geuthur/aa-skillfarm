"""Models for Skillfarm."""

import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from eveuniverse.models import EveType

from allianceauth.eveonline.models import EveCharacter, Token

from skillfarm import app_settings
from skillfarm.hooks import get_extension_logger
from skillfarm.managers.characterskill import CharacterSkillManager
from skillfarm.managers.skillfarmaudit import SkillFarmManager
from skillfarm.managers.skillqueue import SkillqueueManager

logger = get_extension_logger(__name__)


class SkillFarmAudit(models.Model):
    """Character Audit model for app"""

    name = models.CharField(max_length=255, blank=True, null=True)

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
        if (
            self.last_notification is not None
            and self.last_notification
            < timezone.now()
            - datetime.timedelta(days=app_settings.SKILLFARM_NOTIFICATION_COOLDOWN)
        ):
            return False
        if self.last_notification is None:
            return False
        return True


class SkillFarmSetup(models.Model):
    """Skillfarm Character Skill Setup model for app"""

    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255, blank=True, null=True)

    character = models.OneToOneField(
        "SkillFarmAudit", on_delete=models.CASCADE, related_name="skillfarm_setup"
    )

    skillset = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.skillset}'s Skill Setup"

    objects = SkillFarmManager()

    class Meta:
        default_permissions = ()


class CharacterSkill(models.Model):
    """Skillfarm Character Skill model for app"""

    name = models.CharField(max_length=255, blank=True, null=True)

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

    @property
    def is_exc_ready(self) -> bool:
        """Check if skill extraction is ready."""
        try:
            character = SkillFarmSetup.objects.get(character=self.character)
        except SkillFarmSetup.DoesNotExist:
            character = None

        if character and character.skillset is not None:
            skills = CharacterSkill.objects.filter(
                character=self.character,
                eve_type__name__in=character.skillset,
            )
            for skill in skills:
                if skill.trained_skill_level == 5:
                    return True
        return False


class CharacterSkillqueueEntry(models.Model):
    """Skillfarm Skillqueue model for app"""

    name = models.CharField(max_length=255, blank=True, null=True)

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

    # TODO: Add to Notification System
    has_no_skillqueue = models.BooleanField(default=False)
    last_check = models.DateTimeField(default=None, null=True)

    objects = SkillqueueManager()

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.character}-{self.queue_position}"

    @property
    def is_active(self) -> bool:
        """Returns true when this skill is currently being trained"""
        return bool(self.finish_date) and self.finish_date > self.start_date

    @property
    def is_skillqueue_ready(self) -> bool:
        """Check if skill from skillqueue is rdy from end date."""
        if (
            self.is_active
            and self.finish_date <= timezone.now()
            and self.finished_level == 5
        ):
            return True
        return False
