"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as trans
from django.views.decorators.http import require_POST
from esi.decorators import token_required
from eveuniverse.models import EveMarketPrice

from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import EveCharacter

from skillfarm import forms, tasks
from skillfarm.api.helpers import get_character
from skillfarm.hooks import get_extension_logger
from skillfarm.models.skillfarm import SkillFarmAudit, SkillFarmSetup

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
    """Index View"""
    return redirect(
        "skillfarm:skillfarm", request.user.profile.main_character.character_id
    )


@login_required
@permission_required("skillfarm.basic_access")
def skillfarm(request, character_id=None):
    """Main Skillfarm View"""
    if character_id is None:
        character_id = request.user.profile.main_character.character_id

    context = {
        "page_title": "Skillfarm",
        "character_id": character_id,
        "forms": {
            "confirm": forms.ConfirmForm(),
            "skillset": forms.SkillSetForm(),
        },
    }
    context = add_info_to_context(request, context)
    return render(request, "skillfarm/skillfarm.html", context=context)


@login_required
@permission_required("skillfarm.basic_access")
def character_overview(request, character_id=None):
    """Character Overview"""
    if character_id is None:
        character_id = request.user.profile.main_character.character_id

    context = {
        "page_title": "Character Admin",
        "character_id": character_id,
    }
    context = add_info_to_context(request, context)

    return render(request, "skillfarm/overview.html", context=context)


@login_required
@token_required(scopes=SkillFarmAudit.get_esi_scopes())
@permission_required("skillfarm.basic_access")
def add_char(request, token):
    """Add Character to Skillfarm"""
    character = EveCharacter.objects.get_character_by_id(token.character_id)
    char, _ = SkillFarmAudit.objects.update_or_create(
        character=character, defaults={"name": token.character_name}
    )
    tasks.update_character_skillfarm.apply_async(
        args=[char.character.character_id], kwargs={"force_refresh": True}
    )

    msg = trans(
        "{character_name} successfully added or updated to Skillfarm System"
    ).format(
        character_name=char.character.character_name,
    )
    messages.success(request, msg)
    return redirect("skillfarm:index")


@login_required
@permission_required("skillfarm.basic_access")
@require_POST
def remove_char(request, character_id: list):
    """Remove Character from Skillfarm"""
    # Retrieve character_id from GET parameters
    character_id = int(request.POST.get("character_id", 0))

    # Check Permission
    perm, _ = get_character(request, character_id)

    if not perm:
        msg = trans("Permission Denied")
        messages.error(request, msg)
        return redirect("skillfarm:skillfarm", character_id=character_id)

    try:
        character = SkillFarmAudit.objects.get(character__character_id=character_id)
        character.delete()
    except SkillFarmAudit.DoesNotExist:
        msg = trans("Character/s not found")
        messages.error(request, msg)
        return redirect("skillfarm:skillfarm", character_id=character_id)

    msg = trans("{character_name} successfully Deleted").format(
        character_name=character.character.character_name,
    )
    messages.success(request, msg)

    return redirect("skillfarm:skillfarm", character_id=character_id)


@login_required
@permission_required("skillfarm.basic_access")
@require_POST
def switch_alarm(request, character_id: int):
    """Switch Character Notification Alarm"""
    # Check Permission
    perm, __ = get_character(request, character_id)
    form = forms.ConfirmForm(request.POST)
    if form.is_valid():
        if not perm:
            msg = trans("Permission Denied")
            return JsonResponse(
                {"success": False, "message": msg}, status=403, safe=False
            )

        character_id = form.cleaned_data["character_id"]

        try:
            character = SkillFarmAudit.objects.get(character__character_id=character_id)
            character.notification = not character.notification
            character.save()
            msg = trans("Alarm/s successfully updated")
        except SkillFarmAudit.DoesNotExist:
            msg = "Character/s not found"
            return JsonResponse(
                {"success": False, "message": msg}, status=404, safe=False
            )
    else:
        msg = "Invalid Form"
        return JsonResponse({"success": False, "message": msg}, status=400, safe=False)
    return JsonResponse({"success": True, "message": msg}, status=200, safe=False)


@login_required
@permission_required("skillfarm.basic_access")
@require_POST
def skillset(request, character_id: list):
    """Edit Character SkillSet"""
    # Check Permission
    perm, __ = get_character(request, character_id)
    form = forms.SkillSetForm(request.POST)

    if form.is_valid():
        if not perm:
            msg = trans("Permission Denied")
            return JsonResponse(
                {"success": False, "message": msg}, status=403, safe=False
            )
        character_id = form.cleaned_data["character_id"]
        selected_skills = form.cleaned_data["selected_skills"]
        try:
            skillset_list = selected_skills.split(",") if selected_skills else None
            character = SkillFarmAudit.objects.get(character__character_id=character_id)
            SkillFarmSetup.objects.update_or_create(
                character=character, defaults={"skillset": skillset_list}
            )
        except SkillFarmAudit.DoesNotExist:
            msg = trans("Character not found")
            return JsonResponse(
                {"success": False, "message": msg}, status=404, safe=False
            )

        msg = trans("{character_name} Skillset successfully updated").format(
            character_name=character.character.character_name,
        )
    else:
        msg = "Invalid Form"
        return JsonResponse({"success": False, "message": msg}, status=400, safe=False)
    return JsonResponse({"success": True, "message": msg}, status=200, safe=False)


@login_required
@permission_required("skillfarm.basic_access")
def skillfarm_calc(request, character_id=None):
    """Skillfarm Calc View"""
    if character_id is None:
        character_id = request.user.profile.main_character.character_id

    skillfarm_dict = {}
    error = False
    try:
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
    except EveMarketPrice.DoesNotExist:
        EveMarketPrice.objects.update_from_esi()
        error = True

    context = {
        "error": error,
        "character_id": character_id,
        "page_title": "Skillfarm Calc",
        "skillfarm": skillfarm_dict,
    }

    return render(request, "skillfarm/calculator.html", context=context)
