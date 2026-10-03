# Alliance Auth
from allianceauth.authentication.models import User

# AA Skillfarm
from skillfarm.models.skillfarmaudit import SkillFarmAudit


def arabic_number_to_roman(value) -> str:
    """Map to convert arabic to roman numbers (1 to 5 only)"""
    my_map = {0: "-", 1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
    try:
        return my_map[value]
    except KeyError:
        return "-"


def can_view_overview(user: User) -> bool:
    """Check if the user may use the overview of other users' characters."""
    return user.has_perm("skillfarm.basic_access") and (
        user.is_superuser
        or user.has_perm("skillfarm.admin_access")
        or user.has_perm("skillfarm.corp_access")
    )


def get_skillfarm_character(request, character_id, manage: bool = False):
    """
    Get SkillFarmAudit Character and check permissions

    Args:
        request: Django Request Object
        character_id: Character ID of the SkillFarmAudit Character
        manage: Check against `manage_to` instead of `visible_to` (for write actions)
    Returns:
        Tuple of (has_permissions: bool, SkillFarmAudit | None)
    """
    perms = True
    try:
        character = SkillFarmAudit.objects.get(character__character_id=character_id)
    except SkillFarmAudit.DoesNotExist:
        return False, None

    # check access
    if manage:
        allowed = SkillFarmAudit.objects.manage_to(request.user)
    else:
        allowed = SkillFarmAudit.objects.visible_to(request.user)
    if character not in allowed:
        perms = False
    return perms, character
