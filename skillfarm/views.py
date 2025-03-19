"""PvE Views"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from esi.decorators import token_required

from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import EveCharacter

from skillfarm import forms, tasks
from skillfarm.api.helpers import get_character
from skillfarm.hooks import get_extension_logger
from skillfarm.models.prices import EveTypePrice
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
    char = SkillFarmAudit.objects.update_or_create(
        character=character, defaults={"name": token.character_name}
    )[0]
    tasks.update_character_skillfarm.apply_async(
        args=[char.character.character_id], kwargs={"force_refresh": True}
    )

    msg = _(
        "{character_name} successfully added or updated to Skillfarm System"
    ).format(
        character_name=char.character.character_name,
    )
    messages.success(request, msg)
    return redirect("skillfarm:index")


@login_required
@permission_required("skillfarm.basic_access")
@require_POST
def switch_alarm(request, character_id: int):
    """Switch Character Notification Alarm"""
    # Check Permission & If Character Exists
    perm, __ = get_character(request, character_id)
    form = forms.ConfirmForm(request.POST)
    if form.is_valid():
        if not perm:
            msg = _("Permission Denied")
            return JsonResponse(
                {"success": False, "message": msg}, status=403, safe=False
            )

        character_id = form.cleaned_data["character_id"]

        character = SkillFarmAudit.objects.get(character__character_id=character_id)
        character.notification = not character.notification
        character.save()
        msg = _("Alarm successfully updated")
    else:
        msg = "Invalid Form"
        return JsonResponse({"success": False, "message": msg}, status=400, safe=False)
    return JsonResponse({"success": True, "message": msg}, status=200, safe=False)


@login_required
@permission_required("skillfarm.basic_access")
@require_POST
def skillset(request, character_id: list):
    """Edit Character SkillSet"""
    # Check Permission & If Character Exists
    perm, __ = get_character(request, character_id)
    form = forms.SkillSetForm(request.POST)

    if form.is_valid():
        if not perm:
            msg = _("Permission Denied")
            return JsonResponse(
                {"success": False, "message": msg}, status=403, safe=False
            )
        character_id = form.cleaned_data["character_id"]
        selected_skills = form.cleaned_data["selected_skills"]

        skillset_list = selected_skills.split(",") if selected_skills else None
        character = SkillFarmAudit.objects.get(character__character_id=character_id)
        SkillFarmSetup.objects.update_or_create(
            character=character, defaults={"skillset": skillset_list}
        )

        msg = _("{character_name} Skillset successfully updated").format(
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
        plex = EveTypePrice.objects.get(eve_type__id=44992)
        injector = EveTypePrice.objects.get(eve_type__id=40520)
        extractor = EveTypePrice.objects.get(eve_type__id=40519)

        plex_price = float(plex.sell)
        injector_price = float(injector.sell)
        extractor_price = float(extractor.sell)

        monthcalc = (injector_price * 3.5) - (
            (plex_price * 500) + (extractor_price * 3.5)
        )
        month12calc = (injector_price * 3.5) - (
            (plex_price * 300) + (extractor_price * 3.5)
        )
        month24calc = (injector_price * 3.5) - (
            (plex_price * 275) + (extractor_price * 3.5)
        )

        skillfarm_dict["plex"] = plex
        skillfarm_dict["injektor"] = injector
        skillfarm_dict["extratkor"] = extractor

        skillfarm_dict["calc"] = {
            "month": monthcalc,
            "month12": month12calc,
            "month24": month24calc,
        }
    except EveTypePrice.DoesNotExist:
        error = True

    context = {
        "error": {
            "status": error,
            "message": _(
                "An error occurred while fetching the market data. Please inform an admin to fetch Market Data."
            ),
        },
        "character_id": character_id,
        "page_title": "Skillfarm Calc",
        "skillfarm": skillfarm_dict,
    }

    return render(request, "skillfarm/calculator.html", context=context)
