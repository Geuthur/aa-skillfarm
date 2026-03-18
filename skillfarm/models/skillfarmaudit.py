"""Models for Skillfarm."""

# Standard Library
import datetime

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, Token
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError

# Alliance Auth (External Libs)
from eve_sde.models.types import ItemType as EveType

# AA Skillfarm
from skillfarm import __title__, app_settings
from skillfarm.managers.characterskill import SkillManager
from skillfarm.managers.skillfarmaudit import SkillFarmManager
from skillfarm.managers.skillqueue import SkillqueueManager
from skillfarm.models.general import UpdateSectionResult
from skillfarm.models.helpers.update_manager import (
    CharacterUpdateSection,
    UpdateManager,
    UpdateStatus,
)
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


# pylint: disable=too-many-public-methods
class SkillFarmAudit(models.Model):
    """Skillfarm Character Audit model"""

    name = models.CharField(max_length=255, blank=True, null=True)

    active = models.BooleanField(default=True)

    character = models.OneToOneField(
        EveCharacter, on_delete=models.CASCADE, related_name="skillfarm_character"
    )

    notification = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False)
    last_notification = models.DateTimeField(null=True, default=None, blank=True)

    is_read = models.BooleanField(default=False, help_text="Mark Character as read")

    objects: SkillFarmManager = SkillFarmManager()

    def __str__(self):
        return f"{self.character.character_name} - Active: {self.active} - Status: {self.get_status}"

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

    @property
    def notification_icon(self) -> str:
        """Get the notification icon for this character."""
        return format_html(
            render_to_string(
                "skillfarm/partials/icons/notification.html",
                {"status": self.notification},
            )
        )

    @property
    def get_status(self) -> UpdateStatus.description:
        """Get the total update status of this character."""
        if self.active is False:
            return UpdateStatus.DISABLED

        qs = SkillFarmAudit.objects.filter(pk=self.pk).annotate_total_update_status()
        total_update_status = list(qs.values_list("total_update_status", flat=True))[0]
        return UpdateStatus(total_update_status)

    @property
    def last_update(self) -> "CharacterUpdateStatus":
        """Get the last update status of this character."""
        return SkillFarmAudit.objects.last_update_status(self)

    @property
    def is_filtered(self) -> bool:
        """Check if the character has Skill Queue filter active."""
        return (
            self.skillfarm_skillqueue.skill_filtered(self).exists()
            or SkillFarmSetup.objects.filter(
                character=self,
                skillset__isnull=False,
            ).exists()
        )

    @property
    def is_skill_ready(self) -> bool:
        """Check if a character has skills for extraction."""
        return self.skillfarm_skills.extractions(self).exists()

    @property
    def is_skillqueue_ready(self) -> bool:
        """Check if a character has skillqueue ready for extraction."""
        return self.skillfarm_skillqueue.extractions(self).exists()

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

    @property
    def get_skillqueue(self) -> models.QuerySet["CharacterSkillqueueEntry"]:
        """Get the skillqueue for this character."""
        return self.skillfarm_skillqueue.all().select_related("eve_type")

    @property
    def get_skills(self) -> models.QuerySet["CharacterSkill"]:
        """Get the skills for this character."""
        return self.skillfarm_skills.all().select_related("eve_type")

    @property
    def get_skillsetup(self) -> models.QuerySet["SkillFarmSetup"] | None:
        """Get the skill setup for this character."""
        try:
            return self.skillfarm_setup
        except SkillFarmSetup.DoesNotExist:
            return None

    @property
    def extraction_icon(self) -> str:
        if self.is_skill_ready is True:
            return format_html(
                render_to_string("skillfarm/partials/icons/extraction_ready.html")
            )
        if self.is_skillqueue_ready is True:
            return format_html(
                render_to_string("skillfarm/partials/icons/extraction_sb_ready.html")
            )
        return ""

    @property
    def update_manager(self):
        """Return the Update Manager helper for this owner."""
        return UpdateManager(
            character=self,
            update_section=CharacterUpdateSection,
            update_status=CharacterUpdateStatus,
        )

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

    def _generate_notification(self, skill_names: list[str]) -> str:
        """Generate notification for the user."""
        msg = format_lazy(
            "{charname}: {skillname}",
            charname=self.character.character_name,
            skillname=", ".join(skill_names),
        )
        return str(msg)


class SkillFarmSetup(models.Model):
    """Skillfarm Character Skill Setup model for app"""

    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255, blank=True, null=True)

    character = models.OneToOneField(
        SkillFarmAudit, on_delete=models.CASCADE, related_name="skillfarm_setup"
    )

    skillset = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.skillset}'s Skill Setup"

    objects: SkillFarmManager = SkillFarmManager()

    class Meta:
        default_permissions = ()


class CharacterSkill(models.Model):
    """Skillfarm Character Skill model for app"""

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

    objects: SkillManager = SkillManager()

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.character}-{self.eve_type.name}"


class CharacterSkillqueueEntry(models.Model):
    """Skillfarm Skillqueue model for app"""

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

    # TODO: Add to Notification System
    has_no_skillqueue = models.BooleanField(default=False)
    last_check = models.DateTimeField(default=None, null=True)

    objects = SkillqueueManager()

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.character}-{self.queue_position}"


class CharacterUpdateStatus(models.Model):
    """A Model to track the status of the last update."""

    character = models.ForeignKey(
        SkillFarmAudit, on_delete=models.CASCADE, related_name="skillfarm_update_status"
    )
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

    class Meta:
        default_permissions = ()

    def __str__(self) -> str:
        return f"{self.character} - {self.section} - {self.is_success}"

    def need_update(self) -> bool:
        """Check if the update is needed."""
        if not self.is_success or not self.last_update_finished_at:
            needs_update = True
        else:
            section_time_stale = app_settings.SKILLFARM_STALE_TYPES.get(
                self.section, 60
            )
            stale = timezone.now() - timezone.timedelta(minutes=section_time_stale)
            needs_update = self.last_run_finished_at <= stale

        if needs_update and self.has_token_error:
            logger.info(
                "%s: Ignoring update because of token error, section: %s",
                self.character,
                self.section,
            )
            needs_update = False

        return needs_update

    def reset(self) -> None:
        """Reset this update status."""
        self.is_success = None
        self.error_message = ""
        self.has_token_error = False
        self.last_run_at = timezone.now()
        self.last_run_finished_at = None
        self.save()
