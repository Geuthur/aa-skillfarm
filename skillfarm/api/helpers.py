from django.core.exceptions import ObjectDoesNotExist

from allianceauth.eveonline.models import EveCharacter

from skillfarm import models
from skillfarm.hooks import get_extension_logger

logger = get_extension_logger(__name__)


def get_character(request, character_id):
    """Get Character and check permissions"""
    perms = True
    if character_id == 0:
        character_id = request.user.profile.main_character.character_id

    try:
        main_char = EveCharacter.objects.get(character_id=character_id)
    except ObjectDoesNotExist:
        main_char = EveCharacter.objects.select_related(
            "character_ownership",
            "character_ownership__user__profile",
            "character_ownership__user__profile__main_character",
        ).get(character_id=request.user.profile.main_character.character_id)

    # check access
    visible = models.SkillFarmAudit.objects.visible_eve_characters(request.user)
    if main_char not in visible:
        perms = False
    return perms, main_char


def get_alts_queryset(main_char, corporations=None):
    """Get all alts for a main character, optionally filtered by corporations."""
    try:
        linked_corporations = (
            main_char.character_ownership.user.character_ownerships.all()
        )

        if corporations:
            linked_corporations = linked_corporations.filter(
                character__corporation_id__in=corporations
            )

        linked_corporations = linked_corporations.values_list("character_id", flat=True)

        return EveCharacter.objects.filter(id__in=linked_corporations)
    except ObjectDoesNotExist:
        return EveCharacter.objects.filter(pk=main_char.pk)


def _get_linked_characters(corporations):
    linked_chars = EveCharacter.objects.filter(corporation_id__in=corporations)
    linked_chars |= EveCharacter.objects.filter(
        character_ownership__user__profile__main_character__corporation_id__in=corporations
    )
    return (
        linked_chars.select_related(
            "character_ownership", "character_ownership__user__profile__main_character"
        )
        .prefetch_related("character_ownership__user__character_ownerships")
        .order_by("character_name")
    )


def get_main_and_alts_ids_all(corporations: list) -> list:
    """Get all members for given corporations"""
    chars_list = set()

    linked_chars = _get_linked_characters(corporations)

    for char in linked_chars:
        chars_list.add(char.character_id)

    return list(chars_list)
