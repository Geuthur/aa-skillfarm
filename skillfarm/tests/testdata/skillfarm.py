from typing import Tuple

from django.contrib.auth.models import User

from allianceauth.authentication.backends import StateBackend
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils
from app_utils.testing import add_character_to_user

from skillfarm.models.skillfarm import SkillFarmAudit


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


def create_skillfarm_character(character_id: int) -> SkillFarmAudit:
    """Create a Audit Character from EveCharacter"""

    _, character_ownership = create_user_from_evecharacter_with_access(
        character_id, disconnect_signals=True
    )

    audit = SkillFarmAudit.objects.create(
        name=character_ownership.character.character_name,
        character=character_ownership.character,
    )
    return audit
