"""Models for Skillfarm."""

# Standard Library
import datetime
from collections.abc import Callable

# Third Party
from aiopenapi3.errors import HTTPClientError, HTTPServerError

# Django
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, Token
from allianceauth.services.hooks import get_extension_logger
from esi.errors import TokenError
from esi.exceptions import HTTPNotModified

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveType

# AA Skillfarm
from skillfarm import __title__, app_settings
from skillfarm.managers.characterskill import SkillManager
from skillfarm.managers.skillfarmaudit import SkillFarmManager
from skillfarm.managers.skillqueue import SkillqueueManager
from skillfarm.models.general import UpdateSectionResult, _NeedsUpdate

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


# pylint: disable=too-many-public-methods
class SkillFarmAudit(models.Model):
    """Skillfarm Character Audit model"""

    class UpdateSection(models.TextChoices):
        SKILLS = "skills", _("Skills")
        SKILLQUEUE = "skillqueue", _("Skill Queue")

        @classmethod
        def get_sections(cls) -> list[str]:
            """Return list of section values."""
            return [choice.value for choice in cls]

        @property
        def method_name(self) -> str:
            """Return method name for this section."""
            return f"update_{self.value}"

    class UpdateStatus(models.TextChoices):
        DISABLED = "disabled", _("disabled")
        TOKEN_ERROR = "token_error", _("token error")
        ERROR = "error", _("error")
        OK = "ok", _("ok")
        INCOMPLETE = "incomplete", _("incomplete")
        IN_PROGRESS = "in_progress", _("in progress")

        def bootstrap_icon(self) -> str:
            """Return bootstrap corresponding icon class."""
            update_map = {
                status: mark_safe(
                    f"<span class='{self.bootstrap_text_style_class()}' data-tooltip-toggle='skillfarm-tooltip' title='{self.description()}'>⬤</span>"
                )
                for status in [
                    self.DISABLED,
                    self.TOKEN_ERROR,
                    self.ERROR,
                    self.INCOMPLETE,
                    self.IN_PROGRESS,
                    self.OK,
                ]
            }
            return update_map.get(self, "")

        def bootstrap_text_style_class(self) -> str:
            """Return bootstrap corresponding bootstrap text style class."""
            update_map = {
                self.DISABLED: "text-muted",
                self.TOKEN_ERROR: "text-warning",
                self.INCOMPLETE: "text-warning",
                self.IN_PROGRESS: "text-info",
                self.ERROR: "text-danger",
                self.OK: "text-success",
            }
            return update_map.get(self, "")

        def description(self) -> str:
            """Return description for an enum object."""
            update_map = {
                self.DISABLED: _("Update is disabled"),
                self.TOKEN_ERROR: _("One section has a token error during update"),
                self.INCOMPLETE: _("One or more sections have not been updated"),
                self.IN_PROGRESS: _("Update is in progress"),
                self.ERROR: _("An error occurred during update"),
                self.OK: _("Updates completed successfully"),
            }
            return update_map.get(self, "")

    name = models.CharField(max_length=255, blank=True, null=True)

    active = models.BooleanField(default=True)

    character = models.OneToOneField(
        EveCharacter, on_delete=models.CASCADE, related_name="skillfarm_character"
    )

    notification = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False)
    last_notification = models.DateTimeField(null=True, default=None, blank=True)

    objects = SkillFarmManager()

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
        if token:
            return token
        return False

    @property
    def get_status(self) -> UpdateStatus.description:
        """Get the total update status of this character."""
        if self.active is False:
            return self.UpdateStatus.DISABLED

        qs = SkillFarmAudit.objects.filter(pk=self.pk).annotate_total_update_status()
        total_update_status = list(qs.values_list("total_update_status", flat=True))[0]
        return self.UpdateStatus(total_update_status)

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
    def last_update(self) -> UpdateStatus:
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

    def calc_update_needed(self) -> _NeedsUpdate:
        """Calculate if an update is needed."""
        sections: models.QuerySet[CharacterUpdateStatus] = (
            self.skillfarm_update_status.all()
        )
        needs_update = {}
        for section in sections:
            needs_update[section.section] = section.need_update()
        return _NeedsUpdate(section_map=needs_update)

    def reset_update_status(self, section: UpdateSection) -> "CharacterUpdateStatus":
        """Reset the status of a given update section and return it."""
        update_status_obj: CharacterUpdateStatus = (
            self.skillfarm_update_status.get_or_create(
                section=section,
            )[0]
        )
        update_status_obj.reset()
        return update_status_obj

    def reset_has_token_error(self) -> bool:
        """Reset the has_token_error flag for this character."""
        update_status = self.get_status
        if update_status == self.UpdateStatus.TOKEN_ERROR:
            self.skillfarm_update_status.filter(
                has_token_error=True,
            ).update(
                has_token_error=False,
            )
            return True
        return False

    def update_section_if_changed(
        self,
        section: UpdateSection,
        fetch_func: Callable,
        force_refresh: bool = False,
    ):
        """Update the status of a specific section if it has changed."""
        section = self.UpdateSection(section)
        try:
            data = fetch_func(character=self, force_refresh=force_refresh)
            logger.debug("%s: Update has changed, section: %s", self, section.label)
        except HTTPNotModified as exc:
            logger.debug("%s: Update has not changed, section: %s", self, exc)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except HTTPServerError as exc:
            logger.debug("%s: Update has an HTTP internal server error: %s", self, exc)
            return UpdateSectionResult(is_changed=False, is_updated=False)
        except HTTPClientError as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            # TODO ADD DISCORD/AUTH NOTIFICATION?
            logger.error(
                "%s: %s: Update has Client Error: %s %s",
                self,
                section.label,
                error_message,
                exc.status_code,
            )
            return UpdateSectionResult(
                is_changed=False,
                is_updated=False,
                has_token_error=True,
                error_message=error_message,
            )
        return UpdateSectionResult(
            is_changed=True,
            is_updated=True,
            data=data,
        )

    def update_section_log(
        self,
        section: UpdateSection,
        result: UpdateSectionResult,
    ) -> None:
        """Update the status of a specific section."""
        error_message = result.error_message if result.error_message else ""
        is_success = not result.has_token_error
        defaults = {
            "is_success": is_success,
            "error_message": error_message,
            "has_token_error": result.has_token_error,
            "last_run_finished_at": timezone.now(),
        }
        obj: CharacterUpdateStatus = self.skillfarm_update_status.update_or_create(
            section=section,
            defaults=defaults,
        )[0]
        if result.is_updated:
            obj.last_update_at = obj.last_run_at
            obj.last_update_finished_at = timezone.now()
            obj.save()
        status = "successfully" if is_success else "with errors"
        logger.info("%s: %s Update run completed %s", self, section.label, status)

    def perform_update_status(
        self, section: UpdateSection, method: Callable, *args, **kwargs
    ) -> UpdateSectionResult:
        """Perform update status."""
        try:
            result = method(*args, **kwargs)
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {str(exc)}"
            is_token_error = isinstance(exc, (TokenError))
            logger.error(
                "%s: %s: Error during update status: %s",
                self,
                section.label,
                error_message,
                exc_info=not is_token_error,  # do not log token errors
            )
            self.skillfarm_update_status.update_or_create(
                section=section,
                defaults={
                    "is_success": False,
                    "error_message": error_message,
                    "has_token_error": is_token_error,
                    "last_update_at": timezone.now(),
                },
            )
            raise exc
        return result

    def _generate_notification(self, skill_names: list[str]) -> str:
        """Generate notification for the user."""
        msg = _("%(charname)s: %(skillname)s") % {
            "charname": self.character.character_name,
            "skillname": ", ".join(skill_names),
        }
        return msg


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

    objects = SkillFarmManager()

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

    objects = SkillManager()

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
        max_length=32, choices=SkillFarmAudit.UpdateSection.choices, db_index=True
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
