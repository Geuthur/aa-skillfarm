# Third Party
# AA EVE SDE Factory
# Third Party
from evesde_factory.utils import add_character_to_user

# Django
from django.contrib.auth.models import User

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter

# AA Skillfarm
from skillfarm.models.skillfarmaudit import (
    SkillFarmAudit,
)


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
