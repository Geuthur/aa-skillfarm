# Django
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Skillfarm
from skillfarm import __title__
from skillfarm.models.skillfarmaudit import SkillFarmAudit

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def arabic_number_to_roman(value) -> str:
    """Map to convert arabic to roman numbers (1 to 5 only)"""
    my_map = {0: "-", 1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
    try:
        return my_map[value]
    except KeyError:
        return "-"


def get_main_character(request, character_id) -> tuple[bool, EveCharacter]:
    """Get Character and check permissions"""
    perms = True
    try:
        main_char = EveCharacter.objects.get(character_id=character_id)
    except EveCharacter.DoesNotExist:
        main_char = EveCharacter.objects.select_related(
            "character_ownership",
            "character_ownership__user__profile",
            "character_ownership__user__profile__main_character",
        ).get(character_id=request.user.profile.main_character.character_id)

    # check access
    visible = SkillFarmAudit.objects.visible_eve_characters(request.user)
    if main_char not in visible:
        perms = False
    return perms, main_char


def get_character(request, character_id):
    """Get Character and check permissions"""
    perms = True
    try:
        character = SkillFarmAudit.objects.get(character__character_id=character_id)
    except SkillFarmAudit.DoesNotExist:
        return False, None

    # check access
    visible = SkillFarmAudit.objects.visible_to(request.user)
    if character not in visible:
        perms = False
    return perms, character


def get_alts_queryset(main_char, corporations=None):
    """Get all alts for a main character, optionally filtered by corporations."""
    try:
        linked_corporations = main_char.character_ownership.user.character_ownerships.all().select_related(
            "character_ownership"
        )

        if corporations:
            linked_corporations = linked_corporations.filter(
                character__corporation_id__in=corporations
            )

        linked_corporations = linked_corporations.values_list("character_id", flat=True)

        return EveCharacter.objects.filter(id__in=linked_corporations)
    except ObjectDoesNotExist:
        return EveCharacter.objects.filter(pk=main_char.pk)


def generate_toggle_notification_button(character: SkillFarmAudit) -> mark_safe:
    """Generate a toggle notification button for the skillfarm"""
    return format_html(
        render_to_string(
            "skillfarm/partials/buttons/toggle-notification.html",
            {
                "character": character,
            },
        )
    )


def generate_edit_skillsetup_button(character: SkillFarmAudit) -> mark_safe:
    """Generate an edit skillsetup button for the skillfarm"""
    return format_html(
        render_to_string(
            "skillfarm/partials/buttons/edit-skillsetup.html",
            {
                "character": character,
            },
        )
    )


def generate_delete_character_button(character: SkillFarmAudit) -> mark_safe:
    """Generate a delete character button for the skillfarm"""
    return format_html(
        render_to_string(
            "skillfarm/partials/buttons/delete-character.html",
            {
                "character": character,
            },
        )
    )


def generate_skillinfo_button(character: SkillFarmAudit) -> mark_safe:
    """Generate a skillinfo button for the skillfarm"""
    return format_html(
        render_to_string(
            "skillfarm/partials/buttons/skillinfo.html",
            {
                "character": character,
            },
        )
    )


def generate_progressbar_html(progress) -> str:
    """Generate a progress bar HTML"""
    return format_html(
        render_to_string(
            "skillfarm/partials/progressbar.html",
            {
                "progress": f"{progress:.2f}",
            },
        )
    )


def generate_status_icon_html(character: SkillFarmAudit, size: int = 32) -> str:
    """Generate a status icon HTML"""
    return format_html(
        render_to_string(
            "skillfarm/partials/icons/status.html",
            {"character": character, "size": size},
        )
    )
