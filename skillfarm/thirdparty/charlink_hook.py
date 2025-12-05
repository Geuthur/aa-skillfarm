# Third Party
from charlink.app_imports.utils import AppImport, LoginImport

# Django
from django.contrib.auth.models import Permission
from django.db.models import Exists, OuterRef

# Alliance Auth
from allianceauth.authentication.models import User
from allianceauth.eveonline.models import EveCharacter

# AA Skillfarm
from skillfarm import __app_name__
from skillfarm.app_settings import SKILLFARM_APP_NAME
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tasks import update_character


# pylint: disable=unused-argument, duplicate-code
def _add_character_charaudit(request, token):
    skillfarm = SkillFarmAudit.objects.update_or_create(
        character=EveCharacter.objects.get_character_by_id(token.character_id),
        defaults={"name": token.character_name},
    )[0]

    update_character.apply_async(
        args=[skillfarm.pk], kwargs={"force_refresh": True}, priority=6
    )


def _is_character_added_charaudit(character: EveCharacter):
    return SkillFarmAudit.objects.filter(character=character).exists()


def _users_with_perms_charaudit():
    permission = Permission.objects.get(
        content_type__app_label=__app_name__, codename="basic_access"
    )

    users_qs = (
        permission.user_set.all()
        | User.objects.filter(
            groups__in=list(permission.group_set.values_list("pk", flat=True))
        )
        | User.objects.select_related("profile").filter(
            profile__state__in=list(permission.state_set.values_list("pk", flat=True))
        )
        | User.objects.filter(is_superuser=True)
    )
    return users_qs.distinct()


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
