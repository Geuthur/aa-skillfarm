"""PvE Views"""

from datetime import datetime

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as trans
from django.views.decorators.http import require_POST
from esi.decorators import token_required
from eveuniverse.models import EveMarketPrice
from memberaudit.models import Character

from allianceauth.authentication.models import UserProfile

from skillfarm.api.helpers import get_alts_queryset, get_character
from skillfarm.hooks import get_extension_logger
from skillfarm.models import SkillFarmAudit, SkillFarmSetup

logger = get_extension_logger(__name__)


# pylint: disable=unused-argument
def add_info_to_context(request, context: dict) -> dict:
    """Add additional information to the context for the view."""
    theme = None
    try:
        user = UserProfile.objects.get(id=request.user.id)
        theme = user.theme
    except UserProfile.DoesNotExist:
        pass

    new_context = {
        **{"theme": theme},
        **context,
    }
    return new_context


@login_required
@permission_required("skillfarm.basic_access")
def index(request):
    context = {}
    return render(request, "skillfarm/index.html", context=context)


@login_required
@permission_required("skillfarm.basic_access")
def skillfarm(request, character_pk):
    """
    Skillfarm View
    """
    current_year = datetime.now().year
    years = [current_year - i for i in range(6)]

    context = {
        "years": years,
        "character_pk": character_pk,
    }
    context = add_info_to_context(request, context)
    return render(request, "skillfarm/skillfarm.html", context=context)


@login_required
@permission_required("skillfarm.basic_access")
def character_admin(request):
    """
    Character Admin
    """

    context = {}
    context = add_info_to_context(request, context)

    return render(request, "skillfarm/admin/character_admin.html", context=context)


@login_required
@token_required(scopes=SkillFarmAudit.get_esi_scopes())
@permission_required("skillfarm.basic_access")
def add_char(request, token):
    try:
        character = Character.objects.get(
            eve_character__character_id=token.character_id
        )
        char, _ = SkillFarmAudit.objects.update_or_create(
            character=character, defaults={"character": character}
        )
    except Character.DoesNotExist:
        msg = trans("Member Audit Character not found")
        messages.error(request, msg)
        return redirect("skillfarm:skillfarm", character_pk=0)

    msg = trans("{character_name} successfully added to Skillfarm System").format(
        character_name=char.character.eve_character.character_name,
    )
    messages.success(request, msg)
    return redirect("skillfarm:skillfarm", character_pk=0)


@login_required
@permission_required("skillfarm.basic_access")
@require_POST
def remove_char(request, character_id: list):
    # Retrieve character_pk from GET parameters
    character_pk = int(request.POST.get("character_pk", 0))

    # Check Permission
    perm, _ = get_character(request, character_id)

    if not perm:
        msg = trans("Permission Denied")
        messages.error(request, msg)
        return redirect("skillfarm:skillfarm", character_pk=character_pk)

    try:
        character = SkillFarmAudit.objects.get(
            character__eve_character__character_id=character_id
        )
        character.delete()
    except SkillFarmAudit.DoesNotExist:
        msg = trans("Character/s not found")
        messages.error(request, msg)
        return redirect("skillfarm:skillfarm", character_pk=character_pk)

    msg = trans("{character_name} successfully Deleted").format(
        character_name=character.character.eve_character.character_name,
    )
    messages.success(request, msg)

    return redirect("skillfarm:skillfarm", character_pk=character_pk)


@login_required
@permission_required("skillfarm.basic_access")
@require_POST
def switch_alarm(request, character_id: list):
    # Retrieve character_pk from GET parameters
    character_pk = int(request.POST.get("character_pk", 0))

    # Check Permission
    perm, main = get_character(request, character_id)

    if not perm:
        msg = trans("Permission Denied")
        messages.error(request, msg)
        return redirect("skillfarm:skillfarm", character_pk=character_pk)

    if character_id == 0:
        characters = get_alts_queryset(main)
        characters = characters.values_list("character_id", flat=True)
    else:
        characters = [character_id]

    try:
        characters = SkillFarmAudit.objects.filter(
            character__eve_character__character_id__in=characters
        )
        if characters:
            for c in characters:
                c.notification = not c.notification
                c.save()
        else:
            raise SkillFarmAudit.DoesNotExist
    except SkillFarmAudit.DoesNotExist:
        msg = trans("Character/s not found")
        messages.error(request, msg)
        return redirect("skillfarm:skillfarm", character_pk=character_pk)

    msg = trans("Alarm/s successfully updated")
    messages.success(request, msg)

    return redirect("skillfarm:skillfarm", character_pk=character_pk)


@login_required
@permission_required("skillfarm.basic_access")
@require_POST
def skillset(request, character_id: list):
    skillset_data = request.POST.get("skill_set", None)

    # Check Permission
    perm, _ = get_character(request, character_id)

    if not perm:
        msg = trans("Permission Denied")
        messages.error(request, msg)
        return redirect("skillfarm:skillfarm", character_pk=0)

    try:
        skillset_list = skillset_data.split(",") if skillset_data else None
        character = SkillFarmAudit.objects.get(
            character__eve_character__character_id=character_id
        )
        SkillFarmSetup.objects.update_or_create(
            character=character, defaults={"skillset": skillset_list}
        )
    except SkillFarmAudit.DoesNotExist:
        msg = trans("Character not found")
        messages.error(request, msg)
        return redirect("skillfarm:skillfarm", character_pk=0)

    msg = trans("{character_name} Skillset successfully updated").format(
        character_name=character.character.eve_character.character_name,
    )
    messages.success(request, msg)
    return redirect("skillfarm:skillfarm", character_pk=0)


@login_required
@permission_required("voicesofwar.basic_access")
def skillfarm_calc(request):
    skillfarm_dict = {}
    plex = EveMarketPrice.objects.get(eve_type_id=44992)
    injector = EveMarketPrice.objects.get(eve_type_id=40520)
    extractor = EveMarketPrice.objects.get(eve_type_id=40519)

    month = plex.average_price * 500
    month12 = plex.average_price * 300
    month24 = plex.average_price * 275

    monthcalc = (injector.average_price * 3.5) - (
        month + (extractor.average_price * 3.5)
    )
    month12calc = (injector.average_price * 3.5) - (
        month12 + (extractor.average_price * 3.5)
    )
    month24calc = (injector.average_price * 3.5) - (
        month24 + (extractor.average_price * 3.5)
    )

    skillfarm_dict["plex"] = plex
    skillfarm_dict["injektor"] = injector
    skillfarm_dict["extratkor"] = extractor

    skillfarm_dict["calc"] = {
        "month": monthcalc,
        "month12": month12calc,
        "month24": month24calc,
    }

    context = {"skillfarm": skillfarm_dict}

    return render(request, "skillfarm/calc.html", context=context)
