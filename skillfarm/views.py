"""Skillfarm Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger
from esi.decorators import token_required

# AA Skillfarm
from skillfarm import __title__, __version__, tasks
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


@login_required
@permission_required("skillfarm.basic_access")
def react_base(request, *args, **kwargs):  # pylint: disable=unused-argument
    """React Frontend SPA Base View."""
    context = {
        "app_name": "skillfarm",
        "title": "Skillfarm",
        "version": __version__,
    }
    return render(request, "skillfarm/react_skillfarm.html", context=context)


@login_required
@token_required(scopes=SkillFarmAudit.get_esi_scopes())
@permission_required("skillfarm.basic_access")
def add_char(request, token):
    """Add Character to Skillfarm."""
    character = EveCharacter.objects.get_character_by_id(token.character_id)
    char = SkillFarmAudit.objects.update_or_create(
        character=character, defaults={"name": token.character_name}
    )[0]
    tasks.update_character.apply_async(args=[char.pk], kwargs={"force_refresh": True})

    msg = format_lazy(
        _("{character_name} successfully added or updated to Skillfarm System"),
        character_name=char.character.character_name,
    )
    messages.success(request, msg)
    return redirect("skillfarm:react_base")
