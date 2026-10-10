"""Models for Skillfarm."""

# Standard Library
from typing import TYPE_CHECKING

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.authentication.models import User
from allianceauth.eveonline.models import EveCharacter, Token
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError

# Alliance Auth (External Libs)
from eve_sde.models.types import ItemType as EveType

# AA Skillfarm
from skillfarm import __title__, app_settings
from skillfarm.managers.characterskill import SkillManager
from skillfarm.managers.characterupdatestatus import UpdateStatusManager
from skillfarm.managers.skillfarmaudit import SkillFarmManager
from skillfarm.managers.skillqueue import SkillqueueManager
from skillfarm.models.general import UpdateSectionResult
from skillfarm.models.helpers.update_manager import (
    CharacterUpdateSection,
    UpdateManagerMixin,
)
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


# pylint: disable=too-many-public-methods
class SkillFarmAudit(UpdateManagerMixin, models.Model):
    """Skillfarm Character Audit model"""

    update_section_class = CharacterUpdateSection
    update_status_model = "CharacterUpdateStatus"

    if TYPE_CHECKING:  # Give type hints for related names
        skillfarm_skillqueue: SkillqueueManager
        skillfarm_skills: SkillManager
        skillfarm_update_status: UpdateStatusManager
        skillfarm_setup: "SkillFarmSetup"  # OneToOne reverse

    class Meta:
        default_permissions = ()

    objects: SkillFarmManager = SkillFarmManager()

    name = models.CharField(max_length=255, blank=True, null=True)

    active = models.BooleanField(default=True)

    character = models.OneToOneField(
        EveCharacter, on_delete=models.CASCADE, related_name="skillfarm_character"
    )

    notification = models.BooleanField(default=False)
    # Cached / denormalized training status
    is_training = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the character currently has an active training queue.",
    )
    training_finish_date = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        db_index=True,
        help_text="Finish date of the currently training skill.",
    )
    queue_finish_date = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        db_index=True,
        help_text="Finish date of the entire skill queue.",
    )
    current_training_skill = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        help_text="Name and level of current skill in training.",
    )
    total_sp = models.PositiveBigIntegerField(
        default=0,
        help_text="Total accumulated skill points.",
    )

    # Extraction Readiness & Acknowledgment
    extractions_ready_count = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Number of farm skills ready for extraction.",
    )
    extraction_acknowledged = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether ready extractions have been acknowledged by the user.",
    )
    extraction_acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        help_text="Timestamp when extractions were acknowledged.",
    )
    extraction_acknowledged_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="User who acknowledged the ready extractions.",
    )

    # Queue Paused Acknowledgment
    queue_paused_acknowledged = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether paused training has been acknowledged by the user.",
    )

    def update_training_and_extraction_state(self) -> None:
        """
        Recalculate and persist the character's training status, current skill in training,
        total SP, and ready extractions count.
        """
        now = timezone.now()

        # 1. Total SP
        skills_qs = self.skillfarm_skills.all()
        total_sp = (
            skills_qs.aggregate(total=models.Sum("skillpoints_in_skill"))["total"] or 0
        )

        # 2. Training Queue Status
        queue_qs = self.skillfarm_skillqueue.filter(finish_date__isnull=False)
        active_skill = (
            queue_qs.filter(start_date__lte=now, finish_date__gt=now)
            .select_related("eve_type")
            .first()
        )

        if active_skill:
            is_training = True
            training_finish_date = active_skill.finish_date
            level_roman = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}.get(
                active_skill.finished_level, str(active_skill.finished_level)
            )
            current_training_skill = f"{active_skill.eve_type.name} {level_roman}"
            self.queue_paused_acknowledged = False
        else:
            is_training = False
            training_finish_date = None
            current_training_skill = None

        last_queue_item = queue_qs.order_by("-finish_date").first()
        queue_finish_date = (
            last_queue_item.finish_date
            if last_queue_item and last_queue_item.finish_date > now
            else None
        )

        # 3. Extraction readiness
        extractions_from_skills = self.skillfarm_skills.extractions(self).count()
        extractions_from_queue = self.skillfarm_skillqueue.extractions(self).count()
        new_extractions_count = max(extractions_from_skills, extractions_from_queue)

        if new_extractions_count > self.extractions_ready_count or (
            new_extractions_count > 0 and not self.extractions_ready_count
        ):
            self.extraction_acknowledged = False
            self.extraction_acknowledged_at = None
            self.extraction_acknowledged_by = None
        elif new_extractions_count == 0:
            self.extraction_acknowledged = False
            self.extraction_acknowledged_at = None
            self.extraction_acknowledged_by = None

        self.total_sp = total_sp
        self.is_training = is_training
        self.training_finish_date = training_finish_date
        self.queue_finish_date = queue_finish_date
        self.current_training_skill = current_training_skill
        self.extractions_ready_count = new_extractions_count

        self.save(
            update_fields=[
                "total_sp",
                "is_training",
                "training_finish_date",
                "queue_finish_date",
                "current_training_skill",
                "extractions_ready_count",
                "extraction_acknowledged",
                "extraction_acknowledged_at",
                "extraction_acknowledged_by",
                "queue_paused_acknowledged",
            ]
        )

    def acknowledge_extractions(self, user=None) -> None:
        """Mark extractions as acknowledged/reviewed by the user."""
        self.extraction_acknowledged = True
        self.extraction_acknowledged_at = timezone.now()
        if user and user.is_authenticated:
            self.extraction_acknowledged_by = user
        self.save(
            update_fields=[
                "extraction_acknowledged",
                "extraction_acknowledged_at",
                "extraction_acknowledged_by",
            ]
        )

    def acknowledge_queue_paused(self) -> None:
        """Mark paused training state as acknowledged/reviewed by the user."""
        self.queue_paused_acknowledged = True
        self.save(update_fields=["queue_paused_acknowledged"])

    def __str__(self):
        return f"{self.character.character_name}"

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
        if not token:
            raise TokenError(
                f"Token does not exist for {self} with scopes {self.get_esi_scopes()}"
            )
        return token

    @cached_property
    def is_orphan(self) -> bool:
        """
        Return True if this character is an orphan else False.

        An orphan is a character that is not owned anymore by a user.
        """
        return self.character_ownership is None

    @cached_property
    def character_ownership(self) -> bool:
        """
        Return the character ownership object of this character.
        """
        try:
            return self.character.character_ownership
        except ObjectDoesNotExist:
            return None

    def _generate_notification(self, skill_names: list[str]) -> str:
        """Generate notification for the user."""
        msg = format_lazy(
            "{charname}: {skillname}",
            charname=self.character.character_name,
            skillname=", ".join(skill_names),
        )
        return str(msg)

    # Task Area
    def update_skills(self, force_refresh: bool = False) -> UpdateSectionResult:
        """Update skills for this character."""
        return self.skillfarm_skills.update_or_create_esi(
            self, force_refresh=force_refresh
        )

    def update_skillqueue(self, force_refresh: bool = False) -> UpdateSectionResult:
        """Update skillqueue for this character."""
        return self.skillfarm_skillqueue.update_or_create_esi(
            self, force_refresh=force_refresh
        )


class SkillFarmSetup(models.Model):
    """Skillfarm Character Skill Setup model for app"""

    objects: SkillFarmManager = SkillFarmManager()

    class Meta:
        default_permissions = ()

    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255, blank=True, null=True)

    character = models.OneToOneField(
        SkillFarmAudit, on_delete=models.CASCADE, related_name="skillfarm_setup"
    )

    skillset = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.skillset}'s Skill Setup"


class CharacterSkill(models.Model):
    """Skillfarm Character Skill model for app"""

    objects: SkillManager = SkillManager()

    class Meta:
        default_permissions = ()

    name = models.CharField(max_length=255, blank=True, null=True)

    character = models.ForeignKey(
        SkillFarmAudit, on_delete=models.CASCADE, related_name="skillfarm_skills"
    )
    eve_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")

    active_skill_level = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    skillpoints_in_skill = models.PositiveBigIntegerField()
    trained_skill_level = models.PositiveBigIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    def __str__(self) -> str:
        return f"{self.character}-{self.eve_type.name}"


class CharacterSkillqueueEntry(models.Model):
    """Skillfarm Skillqueue model for app"""

    objects: SkillqueueManager = SkillqueueManager()

    class Meta:
        default_permissions = ()

    name = models.CharField(max_length=255, blank=True, null=True)

    character = models.ForeignKey(
        SkillFarmAudit,
        on_delete=models.CASCADE,
        related_name="skillfarm_skillqueue",
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

    def __str__(self) -> str:
        return f"{self.character}-{self.queue_position}"


class CharacterUpdateStatus(models.Model):
    """A Model to track the status of the last update."""

    class Meta:
        default_permissions = ()

    objects: UpdateStatusManager = UpdateStatusManager()

    owner = models.ForeignKey(
        SkillFarmAudit,
        on_delete=models.CASCADE,
        related_name="skillfarm_update_status",
        db_column="character_id",
    )

    @property
    def character(self) -> SkillFarmAudit:
        """Backward-compatible property for character."""
        return self.owner

    @character.setter
    def character(self, value: SkillFarmAudit) -> None:
        self.owner = value

    section = models.CharField(
        max_length=32, choices=CharacterUpdateSection.choices, db_index=True
    )
    is_success = models.BooleanField(default=None, null=True, db_index=True)
    error_message = models.TextField()
    has_token_error = models.BooleanField(default=False)

    last_run_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last run has been started at this time",
    )
    last_run_finished_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last run has been successful finished at this time",
    )
    last_update_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last update has been started at this time",
    )
    last_update_finished_at = models.DateTimeField(
        default=None,
        null=True,
        db_index=True,
        help_text="Last update has been successful finished at this time",
    )

    def __str__(self) -> str:
        return f"{self.owner} - {self.section}"

    def need_update(self) -> bool:
        """Check if the update is needed."""
        if self.has_token_error:
            logger.info(
                "%s: Ignoring update because of token error, section: %s",
                self.owner,
                self.section,
            )
            return False

        if not self.is_success or not self.last_run_finished_at:
            return True

        section_time_stale = app_settings.SKILLFARM_STALE_TYPES.get(self.section, 60)
        stale = timezone.now() - timezone.timedelta(minutes=section_time_stale)
        try:
            return self.last_run_finished_at <= stale
        except AttributeError:
            return True

    def reset(self) -> None:
        """Reset this update status."""
        self.is_success = None
        self.error_message = ""
        self.has_token_error = False
        self.last_run_at = timezone.now()
        self.last_run_finished_at = None
        self.save()


SkillFarmAudit.update_status_model = CharacterUpdateStatus
