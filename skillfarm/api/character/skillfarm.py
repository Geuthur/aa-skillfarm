from ninja import NinjaAPI

from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from allianceauth.authentication.models import UserProfile

from skillfarm.api.character.helpers.skilldetails import (
    _calculate_sum_progress_bar,
    _get_extraction_icon,
    _get_notification_icon,
    _get_skillinfo_actions,
    _skillfarm_actions,
)
from skillfarm.api.character.helpers.skillqueue import _get_character_skillqueue
from skillfarm.api.character.helpers.skills import _get_character_skills
from skillfarm.api.helpers import (
    get_alts_queryset,
    get_character,
    get_main_character,
)
from skillfarm.helpers import lazy
from skillfarm.hooks import get_extension_logger
from skillfarm.models.skillfarm import SkillFarmAudit, SkillFarmSetup

logger = get_extension_logger(__name__)


class SkillFarmApiEndpoints:
    tags = ["SkillFarm"]

    # pylint: disable=too-many-statements, too-many-locals
    def __init__(self, api: NinjaAPI):
        @api.get(
            "{character_id}/overview/",
            response={200: dict, 403: str},
            tags=self.tags,
        )
        # pylint: disable=unused-argument
        def get_character_overview(request, character_id: int):
            """Get Character SkillFarm Overview"""
            chars_visible = SkillFarmAudit.objects.visible_eve_characters(request.user)

            if chars_visible is None:
                return 403, "Permission Denied"

            chars_ids = chars_visible.values_list("character_id", flat=True)

            users_char_ids = UserProfile.objects.filter(
                main_character__isnull=False, main_character__character_id__in=chars_ids
            )

            overview_dict = {}

            for character in users_char_ids:
                # pylint: disable=broad-exception-caught
                try:
                    button = format_html(
                        '<a href="{}"><button class="btn btn-primary btn-sm" title="'
                        + _("Show Skillfarm")
                        + '" data-tooltip-toggle="skillfarm-tooltip" ><span class="fas fa-eye"></span></button></a>',
                        reverse(
                            "skillfarm:skillfarm",
                            kwargs={
                                "character_id": character.main_character.character_id
                            },
                        ),
                    )

                    portrait = lazy.get_character_portrait_url(
                        character_id=character.main_character.character_id,
                        character_name=character.main_character.character_name,
                        as_html=True,
                    )

                    overview_dict[character.main_character.character_id] = {
                        "portrait": portrait,
                        "character_id": character.main_character.character_id,
                        "character_name": character.main_character.character_name,
                        "corporation_id": character.main_character.corporation_id,
                        "corporation_name": character.main_character.corporation_name,
                        "action": button,
                    }
                except AttributeError:
                    continue

            return overview_dict

        @api.get(
            "{character_id}/details/",
            response={200: dict, 403: str},
            tags=self.tags,
        )
        def get_details(request, character_id: int):
            """Get Character SkillFarm Details"""
            perm, main = get_main_character(request, character_id)

            if perm is False:
                return 403, "Permission Denied"

            characters = get_alts_queryset(main)

            audit_chars = SkillFarmAudit.objects.filter(
                character__in=characters
            ).select_related("character")

            details_dict = []
            inactive_dict = []

            for character in audit_chars:
                char_portrait = lazy.get_character_portrait_url(
                    character_id=character.character.character_id,
                    character_name=character.character.character_name,
                    as_html=True,
                )
                notification = _get_notification_icon(character.notification)

                char = f"{char_portrait} {character.character.character_name} {notification}"

                skills = _get_character_skills(character)
                skillqueue = _get_character_skillqueue(character)

                skillextraction = _get_extraction_icon(
                    skills=skills["is_extraction_ready"],
                    skillqueue=skillqueue["skillqueue_ready"],
                )

                skillinfo = _get_skillinfo_actions(character=character, request=request)

                skillinfo_html = f"{skillinfo} {skillextraction}"

                actions = _skillfarm_actions(
                    character=character, perms=perm, request=request
                )

                details = {
                    "character": {
                        "character_html": char,
                        "character_id": character.character.character_id,
                        "character_name": character.character.character_name,
                    },
                    "details": {
                        "active": character.active,
                        "notification": character.notification,
                        "last_update": lazy.str_normalize_time(
                            evetime=character.last_update_skillqueue, hours=True
                        ),
                        "is_extraction_ready": skillinfo_html,
                        "is_filter": skillqueue.get("is_filter", ""),
                    },
                    "actions": actions,
                }

                if (
                    skills["skills"]
                    and not skillqueue["skillqueue"]
                    or skillqueue["is_training"] is False
                ):
                    details["details"]["progress"] = _("No Active Training")
                    inactive_dict.append(details)
                else:
                    details["details"]["progress"] = _calculate_sum_progress_bar(
                        skillqueue=skillqueue["skillqueue"], skills=skills["skills"]
                    )
                    details_dict.append(details)

            output = {
                "details": details_dict,
                "inactive": inactive_dict,
            }

            return output

        @api.get(
            "{character_id}/skillsetup/",
            response={200: dict, 403: str},
            tags=self.tags,
        )
        def get_skillsetup(request, character_id: int):
            """Get Character SkillSet"""
            perm, character = get_character(request, character_id)

            if perm is False:
                return 403, "Permission Denied"

            output = {}

            try:
                skillfilter = SkillFarmSetup.objects.get(character=character)
                skillset = skillfilter.skillset
                output = {
                    "character_id": character.character.character_id,
                    "character_name": character.character.character_name,
                    "skillset": skillset,
                }
            except SkillFarmSetup.DoesNotExist:
                pass

            return output

        @api.get(
            "{character_id}/skillinfo/",
            response={200: dict, 403: str},
            tags=self.tags,
        )
        def get_skillinfo_details(request, character_id: int):
            """Get Character Skills and SkillQueue"""
            perm, character = get_character(request, character_id)

            if perm is False:
                return 403, "Permission Denied"

            skills = _get_character_skills(character)
            skillqueue = _get_character_skillqueue(character)

            context = {
                "title": _("Skill Info"),
                "character_id": character.character.character_id,
                "character_name": character.character.character_name,
                "skillqueue": skillqueue["skillqueue"],
                "skills": skills["skills"],
            }

            return render(
                request, "skillfarm/partials/modals/view_skillqueue.html", context
            )
