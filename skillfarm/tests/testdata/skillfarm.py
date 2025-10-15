# Standard Library
from typing import List, Optional, Tuple

# Django
from django.contrib.auth.models import User
from django.db.models import Q

# Alliance Auth
from allianceauth.authentication.backends import StateBackend
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils

# Alliance Auth (External Libs)
from app_utils.testing import add_character_to_user
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
    """Create a Skillfarm Character from EveCharacter"""
    params = {"name": eve_character.character_name, "character": eve_character}
    params.update(kwargs)
    character = SkillFarmAudit(**params)
    character.save()
    return character


def create_update_status(
    character_audit: SkillFarmAudit, **kwargs
) -> CharacterUpdateStatus:
    """Create a Update Status for a Character Audit"""
    params = {
        "character": character_audit,
    }
    params.update(kwargs)
    update_status = CharacterUpdateStatus(**params)
    update_status.save()
    return update_status


def create_user_from_evecharacter_with_access(
    character_id: int, disconnect_signals: bool = True
) -> tuple[User, CharacterOwnership]:
    """Create user with access from an existing eve character and use it as main."""
    auth_character = EveCharacter.objects.get(character_id=character_id)
    username = StateBackend.iterate_username(auth_character.character_name)
    user = AuthUtils.create_user(username, disconnect_signals=disconnect_signals)
    user = AuthUtils.add_permission_to_user_by_name(
        "skillfarm.basic_access", user, disconnect_signals=disconnect_signals
    )
    character_ownership = add_character_to_user(
        user,
        auth_character,
        is_main=True,
        scopes=SkillFarmAudit.get_esi_scopes(),
        disconnect_signals=disconnect_signals,
    )
    return user, character_ownership


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
    eve_character = user.profile.main_character
    if not eve_character:
        raise ValueError("User needs to have a main character.")

    kwargs.update({"eve_character": eve_character})
    return create_character(**kwargs)


def create_skillfarm_character(character_id: int, **kwargs) -> SkillFarmAudit:
    """Create a Audit Character from a existing EveCharacter"""

    _, character_ownership = create_user_from_evecharacter_with_access(
        character_id, disconnect_signals=True
    )
    return create_character(character_ownership.character, **kwargs)


def create_skillsetup_character(character_id: int, skillset: list) -> SkillFarmSetup:
    """Create a SkillSet for Skillfarm Audit Character"""
    audit = SkillFarmAudit.objects.get(
        character__character_id=character_id,
    )

    skillsetup = SkillFarmSetup(
        character=audit,
        skillset=skillset,
    )
    skillsetup.save()

    return skillsetup


def create_evetypeprice(evetype_id: int, **kwargs) -> EveType:
    params = {
        "eve_type": EveType.objects.get(id=evetype_id),
    }
    params.update(kwargs)
    price = EveTypePrice(**params)
    price.save()
    return price


def create_skill_character(
    character_id: int,
    evetype_id: int,
    skillpoints: int,
    active_level: int = 5,
    trained_level: int = 5,
) -> CharacterSkill:
    """Create a Skill for Skillfarm Audit Character"""
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


def add_auth_character_to_user(
    user: User, character_id: int, disconnect_signals: bool = True
) -> CharacterOwnership:
    auth_character = EveCharacter.objects.get(character_id=character_id)
    return add_character_to_user(
        user,
        auth_character,
        is_main=False,
        scopes=SkillFarmAudit.get_esi_scopes(),
        disconnect_signals=disconnect_signals,
    )


def add_skillfarmaudit_character_to_user(
    user: User, character_id: int, disconnect_signals: bool = True, **kwargs
) -> SkillFarmAudit:
    character_ownership = add_auth_character_to_user(
        user,
        character_id,
        disconnect_signals=disconnect_signals,
    )
    return create_character(character_ownership.character, **kwargs)
