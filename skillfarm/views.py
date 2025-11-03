"""PvE Views"""

# Standard Library
import json

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

# Alliance Auth
from allianceauth.authentication.models import UserProfile
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger
from esi.decorators import token_required

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Skillfarm
from skillfarm import __title__, forms, tasks
from skillfarm.api.helpers.core import get_character
from skillfarm.models.prices import EveTypePrice
from skillfarm.models.skillfarmaudit import SkillFarmAudit, SkillFarmSetup
from skillfarm.tasks import update_all_skillfarm

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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
def admin(request):
    """Admin View"""
    context = {
        "page_title": "Admin",
    }

    if not request.user.is_superuser:
        messages.error(request, _("You do not have permission to access this page."))
        return redirect("skillfarm:index")

    if request.method == "POST":
        force_refresh = False
        if request.POST.get("force_refresh", False):
            force_refresh = True
        if request.POST.get("run_char_updates"):
            messages.info(request, _("Queued Update All Characters"))
            update_all_skillfarm.apply_async(
                kwargs={"force_refresh": force_refresh}, priority=7
            )
    return render(request, "skillfarm/admin.html", context=context)


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
def character_overview(request):
    """Character Overview"""
    context = {
        "page_title": "Character Overview",
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
    tasks.update_character.apply_async(args=[char.pk], kwargs={"force_refresh": True})

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
def delete_character(request, character_id: int):
    """Delete Character"""
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
        character.delete()
        msg = _("{character_name} successfully deleted").format(
            character_name=character.character.character_name,
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

        character = SkillFarmAudit.objects.get(character__character_id=character_id)

        try:
            skills_data = json.loads(selected_skills)
            filtered = [
                entry["value"]
                for entry in skills_data
                if entry.get("selected") is True and entry.get("value")
            ]
            skillset_list = filtered if filtered else None
            SkillFarmSetup.objects.update_or_create(
                character=character, defaults={"skillset": skillset_list}
            )
        except Exception:  # pylint: disable=broad-except
            msg = _("Invalid JSON format")
            return JsonResponse(
                {"success": False, "message": msg}, status=400, safe=False
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
