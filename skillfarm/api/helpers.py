from typing import Optional

from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from allianceauth.eveonline.models import EveCharacter

from skillfarm.hooks import get_extension_logger
from skillfarm.models.skillfarm import SkillFarmAudit, SkillFarmSetup

logger = get_extension_logger(__name__)


def arabic_number_to_roman(value) -> str:
    """Map to convert arabic to roman numbers (1 to 5 only)"""
    my_map = {0: "-", 1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
    try:
        return my_map[value]
    except KeyError:
        return "-"


def get_main_character(request, character_id):
    """Get Character and check permissions"""
    perms = True
    try:
        main_char = EveCharacter.objects.get(character_id=character_id)
    except ObjectDoesNotExist:
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
    except ObjectDoesNotExist:
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


def get_skillset(character: SkillFarmAudit) -> Optional[dict]:
    """Get the skillset for the character"""
    try:
        skillfilter = SkillFarmSetup.objects.get(character=character)
        return skillfilter.skillset
    except SkillFarmSetup.DoesNotExist:
        return None


def generate_button(template, queryset, settings, request) -> mark_safe:
    """Generate a html button for the tax system"""
    return format_html(
        render_to_string(
            template,
            {
                "queryset": queryset,
                "settings": settings,
            },
            request=request,
        )
    )


# pylint: disable=too-many-positional-arguments
def generate_settings(
    title: str, icon: str, color: str, text: str, modal: str, action: str, ajax: str
) -> dict:
    """Generate a settings dict for the tax system"""
    return {
        "title": title,
        "icon": icon,
        "color": color,
        "text": text,
        "modal": modal,
        "action": action,
        "ajax": ajax,
    }
