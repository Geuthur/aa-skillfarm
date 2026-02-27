# Standard Library
import datetime as dt
import random
import string
from typing import List, Optional

# Django
from django.contrib.auth.models import User
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.tests.auth_utils import AuthUtils
from esi.models import Scope, Token

# AA Skillfarm
from skillfarm.models.prices import EveType, EveTypePrice
from skillfarm.models.skillfarmaudit import (
    CharacterSkill,
    CharacterUpdateStatus,
    SkillFarmAudit,
    SkillFarmSetup,
)


def dt_eveformat(my_dt: dt.datetime) -> str:
    """Convert datetime to EVE Online ISO format (YYYY-MM-DDTHH:MM:SS)

    Args:
        my_dt (datetime): Input datetime
    Returns:
        str: datetime in EVE Online ISO format
    """

    my_dt_2 = dt.datetime(
        my_dt.year, my_dt.month, my_dt.day, my_dt.hour, my_dt.minute, my_dt.second
    )

    return my_dt_2.isoformat()


def random_string(char_count: int) -> str:
    """returns a random string of given length"""
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(char_count)
    )


def _generate_token(
    character_id: int,
    character_name: str,
    owner_hash: str | None = None,
    access_token: str = "access_token",
    refresh_token: str = "refresh_token",
    scopes: list | None = None,
    timestamp_dt: dt.datetime | None = None,
    expires_in: int = 1200,
) -> dict:
    """Generates the input to create a new SSO test token.

    Args:
        character_id (int): Character ID
        character_name (str): Character Name
        owner_hash (Optional[str], optional): Character Owner Hash. Defaults to None.
        access_token (str, optional): Access Token string. Defaults to "access_token".
        refresh_token (str, optional): Refresh Token string. Defaults to "refresh_token".
        scopes (Optional[list], optional): List of scope names. Defaults to None.
        timestamp_dt (Optional[dt.datetime], optional): Timestamp datetime. Defaults to None.
        expires_in (int, optional): Expiry time in seconds. Defaults to 1200
    Returns:
        dict: The generated token dict
    """
    if timestamp_dt is None:
        timestamp_dt = dt.datetime.utcnow()
    if scopes is None:
        scopes = [
            "esi-mail.read_mail.v1",
            "esi-wallet.read_character_wallet.v1",
            "esi-universe.read_structures.v1",
        ]
    if owner_hash is None:
        owner_hash = random_string(28)
    token = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": refresh_token,
        "timestamp": int(timestamp_dt.timestamp()),
        "CharacterID": character_id,
        "CharacterName": character_name,
        "ExpiresOn": dt_eveformat(timestamp_dt + dt.timedelta(seconds=expires_in)),
        "Scopes": " ".join(list(scopes)),
        "TokenType": "Character",
        "CharacterOwnerHash": owner_hash,
        "IntellectualProperty": "EVE",
    }
    return token


def _store_as_Token(token: dict, user: object) -> Token:
    """Stores a generated token dict as Token object for given user

    Args:
        token (dict): Generated token dict
        user (User): Alliance Auth User
    Returns:
        Token: The created Token object
    """
    character_tokens = user.token_set.filter(character_id=token["CharacterID"])
    if character_tokens.exists():
        token["CharacterOwnerHash"] = character_tokens.first().character_owner_hash
    obj = Token.objects.create(
        access_token=token["access_token"],
        refresh_token=token["refresh_token"],
        user=user,
        character_id=token["CharacterID"],
        character_name=token["CharacterName"],
        token_type=token["TokenType"],
        character_owner_hash=token["CharacterOwnerHash"],
    )
    for scope_name in token["Scopes"].split(" "):
        scope, _ = Scope.objects.get_or_create(name=scope_name)
        obj.scopes.add(scope)
    return obj


def add_new_token(
    user: User,
    character: EveCharacter,
    scopes: list[str] | None = None,
    owner_hash: str | None = None,
) -> Token:
    """Generate a new token for a user based on a character and makes the given user it's owner.

    Args:
        user: Alliance Auth User
        character: EveCharacter to create the token for
        scopes: list of scope names
        owner_hash: optional owner hash to use for the token
    Returns:
        Token: The created Token object
    """
    return _store_as_Token(
        _generate_token(
            character_id=character.character_id,
            character_name=character.character_name,
            owner_hash=owner_hash,
            scopes=scopes,
        ),
        user,
    )


def add_character_to_user(
    user: User,
    character: EveCharacter,
    is_main: bool = False,
    scopes: list[str] | None = None,
    disconnect_signals: bool = False,
) -> CharacterOwnership:
    """Add an existing :class:`EveCharacter` to a User, optionally as main character.

    Args:
        user (User): The User to whom the EveCharacter will be added.
        character (EveCharacter): The EveCharacter to add to the User.
        is_main (bool, optional): Whether to set the EveCharacter as the User's main
            character. Defaults to ``False``.
        scopes (list[str] | None, optional): List of scope names to assign to the
            character's token. If ``None``, defaults to `["publicData"]`. Defaults to ``None``.
        disconnect_signals (bool, optional): Whether to disconnect signals during
            the addition. Defaults to ``False``.
    Returns:
        CharacterOwnership: The created CharacterOwnership instance.
    """

    if not scopes:
        scopes = ["publicData"]

    if disconnect_signals:
        AuthUtils.disconnect_signals()

    add_new_token(user, character, scopes)

    if is_main:
        user.profile.main_character = character
        user.profile.save()
        user.save()

    if disconnect_signals:
        AuthUtils.connect_signals()

    return CharacterOwnership.objects.get(user=user, character=character)


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


def create_skillfarm_character_with_user(character_id: int, **kwargs) -> SkillFarmAudit:
    """Create a Skillfarm Audit Character along with a new Alliance Auth User.

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
