from charlink.app_imports.utils import AppImport, LoginImport

from django.contrib.auth.models import Permission
from django.db.models import Exists, OuterRef

from allianceauth.eveonline.models import EveCharacter
from app_utils.allianceauth import users_with_permission

from skillfarm.app_settings import SKILLFARM_APP_NAME
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tasks import update_character_skillfarm


# pylint: disable=unused-argument, duplicate-code
def _add_character_charaudit(request, token):
    SkillFarmAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id)
    )
    update_character_skillfarm.apply_async(
        args=[token.character_id], kwargs={"force_refresh": True}, priority=6
    )


def _is_character_added_charaudit(character: EveCharacter):
    return SkillFarmAudit.objects.filter(character=character).exists()


def _users_with_perms_charaudit():
    return users_with_permission(
        Permission.objects.get(
            content_type__app_label="skillfarm", codename="basic_access"
        )
    )


app_import = AppImport(
    "skillfarm",
    [
        LoginImport(
            app_label="skillfarm",
            unique_id="default",
            field_label=SKILLFARM_APP_NAME,
            add_character=_add_character_charaudit,
            scopes=SkillFarmAudit.get_esi_scopes(),
            check_permissions=lambda user: user.has_perm("skillfarm.basic_access"),
            is_character_added=_is_character_added_charaudit,
            is_character_added_annotation=Exists(
                SkillFarmAudit.objects.filter(character_id=OuterRef("pk"))
            ),
            get_users_with_perms=_users_with_perms_charaudit,
        ),
    ],
)
