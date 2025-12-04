# Standard Library
from typing import List, Optional, Tuple

# Third Party
from app_utils.testing import add_character_to_user

# Django
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.backends import StateBackend
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils

# Alliance Auth (External Libs)
from eveuniverse.models import EveType

# AA Skillfarm
from skillfarm.models.prices import EveTypePrice
from skillfarm.models.skillfarmaudit import (
    CharacterSkill,
    CharacterUpdateStatus,
    SkillFarmAudit,
    SkillFarmSetup,
)


def create_character(eve_character: EveCharacter, **kwargs) -> SkillFarmAudit:
    """Create a Skillfarm Character from an :class:`EveCharacter`.

    Args:
        eve_character (EveCharacter): EveCharacter object used as the basis
            for the created SkillFarmAudit.
    :Keyword Arguments:
        Any additional fields to set on the SkillFarmAudit instance.
    Returns:
        SkillFarmAudit: The created SkillFarmAudit instance.
    """
    params = {"name": eve_character.character_name, "character": eve_character}
    params.update(kwargs)
    character = SkillFarmAudit(**params)
    character.save()
    return character


def create_update_status(
    character_audit: SkillFarmAudit, section: str, error_message: str, **kwargs
) -> CharacterUpdateStatus:
    """Create a Update Status for a Character Audit

    Args:
        character_audit (SkillFarmAudit): The SkillFarmAudit instance to
            associate with the CharacterUpdateStatus.
        section (str): Section name.
        error_message (str): Error message if any.
    :Keyword Arguments:
        Any additional fields to set on the CharacterUpdateStatus instance.
    Returns:
        CharacterUpdateStatus: The created CharacterUpdateStatus instance.
    """
    params = {
        "character": character_audit,
        "section": section,
        "error_message": error_message,
    }
    params.update(kwargs)
    update_status = CharacterUpdateStatus(**params)
    update_status.save()
    return update_status


def create_user_from_evecharacter(
    character_id: int,
    permissions: list[str] | None = None,
    scopes: list[str] | None = None,
) -> tuple[User, CharacterOwnership]:
    """Create new allianceauth user from EveCharacter object.

    Args:
        character_id: ID of eve character
        permissions: list of permission names, e.g. `"my_app.my_permission"`
        scopes: list of scope names
    """
    auth_character = EveCharacter.objects.get(character_id=character_id)
    user = AuthUtils.create_user(auth_character.character_name.replace(" ", "_"))
    character_ownership = add_character_to_user(
        user, auth_character, is_main=True, scopes=scopes
    )
    if permissions:
        for permission_name in permissions:
            user = AuthUtils.add_permission_to_user_by_name(permission_name, user)
    return user, character_ownership


def create_skillfarm_character_from_user(user: User, **kwargs) -> SkillFarmAudit:
    """Create a Skillfarm Audit Character from an existing Alliance Auth User.

    Args:
        user (User): The Alliance Auth User to create the SkillFarmAudit for.
    :Keyword Arguments:
        Any additional fields to set on the SkillFarmAudit instance.
    Returns:
        SkillFarmAudit: The created SkillFarmAudit instance.
    """
    eve_character = user.profile.main_character
    if not eve_character:
        raise ValueError("User needs to have a main character.")

    kwargs.update({"eve_character": eve_character})
    return create_character(**kwargs)


def create_skillfarm_character(character_id: int, **kwargs) -> SkillFarmAudit:
    """Create a Audit Character from a existing EveCharacter.

    Args:
        character_id (int): The character ID of the EveCharacter to create the SkillFarmAudit for.
    :Keyword Arguments:
        Any additional fields to set on the SkillFarmAudit instance.
    Returns:
        SkillFarmAudit: The created SkillFarmAudit instance.
    """
    character_ownership = create_user_from_evecharacter(
        character_id, permissions=["skillfarm.basic_access"]
    )[1]
    return create_character(character_ownership.character, **kwargs)


def create_skillsetup_character(character_id: int, skillset: list) -> SkillFarmSetup:
    """Create a SkillSet for Skillfarm Audit Character.

    Args:
        character_id (int): The character ID of the EveCharacter.
        skillset (list): List of skill IDs to include in the SkillFarmSetup.
    """
    audit = SkillFarmAudit.objects.get(
        character__character_id=character_id,
    )

    skillsetup = SkillFarmSetup(
        character=audit,
        skillset=skillset,
    )
    skillsetup.save()

    return skillsetup


def create_eve_type_price(
    name: str, eve_type_id: int, buy: int, sell: int, updated_at: timezone.datetime
) -> EveTypePrice:
    """Create a EveTypePrice for an EveType.

    Args:
        name (str): Name of the EveTypePrice.
        eve_type_id (int): The ID of the EveType.
        buy (int): Buy price.
        sell (int): Sell price.
    Returns:
        EveTypePrice: The created EveTypePrice instance.
    """
    params = {
        "name": name,
        "eve_type": EveType.objects.get(id=eve_type_id),
        "buy": buy,
        "sell": sell,
        "updated_at": updated_at,
    }
    price = EveTypePrice(**params)
    price.save()
    return price


def create_character_skill(
    character_id: int,
    evetype_id: int,
    skillpoints: int = 0,
    active_level: int = 5,
    trained_level: int = 5,
) -> CharacterSkill:
    """Create a Skill for Skillfarm Audit Character.

    Args:
        character_id (int): The character ID of the EveCharacter.
        evetype_id (int): The ID of the EveType representing the skill.
        skillpoints (int, optional): The number of skillpoints in the skill. Defaults to 0.
        active_level (int, optional): The active skill level. Defaults to 5.
        trained_level (int, optional): The trained skill level. Defaults to 5.
    Returns:
        CharacterSkill: The created CharacterSkill instance.
    """
    audit = SkillFarmAudit.objects.get(
        character__character_id=character_id,
    )

    skill = CharacterSkill(
        character=audit,
        eve_type=EveType.objects.get(id=evetype_id),
        skillpoints_in_skill=skillpoints,
        active_skill_level=active_level,
        trained_skill_level=trained_level,
    )
    skill.save()

    return skill


def add_permission_to_user(
    user: User,
    permissions: list[str] | None = None,
) -> User:
    """Add permission to existing allianceauth user.
    Args:
        user: Alliance Auth User
        permissions: list of permission names, e.g. `"my_app.my_permission"`
    Returns:
        User: Updated Alliance Auth User
    """
    if permissions:
        for permission_name in permissions:
            user = AuthUtils.add_permission_to_user_by_name(permission_name, user)
            return user
    raise ValueError("No permissions provided to add to user.")


def add_alt_character_to_user(
    user: User, character_id: int, disconnect_signals: bool = True
) -> CharacterOwnership:
    """Add an existing EveCharacter to a User.

    Args:
        user (User): The User to whom the EveCharacter will be added.
        character_id (int): The character ID of the EveCharacter to add.
        disconnect_signals (bool, optional): Whether to disconnect signals during
            the addition. Defaults to ``True``.
    Returns:
        CharacterOwnership: The created CharacterOwnership instance.
    """
    auth_character = EveCharacter.objects.get(character_id=character_id)
    return add_character_to_user(
        user,
        auth_character,
        is_main=False,
        scopes=SkillFarmAudit.get_esi_scopes(),
        disconnect_signals=disconnect_signals,
    )
