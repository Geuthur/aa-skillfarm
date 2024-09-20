from collections import defaultdict
from typing import List

from memberaudit.helpers import arabic_number_to_roman
from memberaudit.models.character_sections_3 import CharacterSkillqueueEntry
from ninja import NinjaAPI

from django.db.models import Q

from allianceauth.authentication.models import UserProfile

from skillfarm.api import schema
from skillfarm.api.helpers import get_alts_queryset, get_character
from skillfarm.hooks import get_extension_logger
from skillfarm.models import SkillFarmAudit, SkillFarmSetup

logger = get_extension_logger(__name__)


# pylint: disable=duplicate-code
class SkillFarmApiEndpoints:
    tags = ["SkillFarm"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "account/{character_id}/skillfarm/",
            response={200: List[schema.SkillFarm], 403: str},
            tags=self.tags,
        )
        # pylint: disable=too-many-locals
        def get_character_skillfarm(request, character_id: int):
            request_main = request.GET.get("main", False)
            perm, main = get_character(request, character_id)

            if perm is False:
                return 403, "Permission Denied"

            # Create the Ledger
            if character_id == 0 or request_main:
                characters = get_alts_queryset(main)
            else:
                characters = [main]

            skills_dict = defaultdict(list)
            output = []

            # Get all Characters
            audit = SkillFarmAudit.objects.filter(
                character__eve_character__in=characters
            )
            audit_list = audit.values_list(
                "character__eve_character__character_id", flat=True
            )

            filters = Q(character__eve_character__character_id__in=audit_list)

            # Filter Skills from Skillset
            filter_skills = SkillFarmSetup.objects.filter(
                character__character__eve_character__character_id__in=audit_list
            )

            skill_names = []
            for skill in filter_skills:
                if skill.skillset is None:
                    continue
                skill_names.extend(skill.skillset)

            if skill_names:
                filters &= Q(eve_type__name__in=skill_names)

            # Get all Skill Queue from Characters
            skills = CharacterSkillqueueEntry.objects.select_related(
                "character__eve_character", "eve_type"
            ).filter(filters)

            # Add the skillqueue to the dict
            for entry in skills:
                character = entry.character.eve_character
                level = arabic_number_to_roman(entry.finished_level)

                dict_data = {
                    "skill": f"{entry.eve_type.name} {level}",
                    "start_sp": entry.level_start_sp,
                    "end_sp": entry.level_end_sp,
                    "trained_sp": entry.training_start_sp,
                    "start_date": entry.start_date,
                    "finish_date": entry.finish_date,
                }

                skills_dict[character].append(dict_data)

            # Add the skillsque to the output
            for character, skills in skills_dict.items():
                # Get Audit Data
                audit_entry = audit.get(
                    character__eve_character__character_id=character.character_id
                )
                output.append(
                    {
                        "character_id": character.character_id,
                        "character_name": character.character_name,
                        "corporation_id": character.corporation_id,
                        "corporation_name": character.corporation_name,
                        "active": audit_entry.active,
                        "notification": audit_entry.notification,
                        "last_update": audit_entry.last_update,
                        "skills": skills,
                    }
                )

            return output

        @api.get(
            "account/skillfarm/admin/",
            response={200: List[schema.CharacterAdmin], 403: str},
            tags=self.tags,
        )
        def get_character_admin(request):
            chars_visible = SkillFarmAudit.objects.visible_eve_characters(request.user)

            if chars_visible is None:
                return 403, "Permission Denied"

            chars_ids = chars_visible.values_list("character_id", flat=True)

            users_char_ids = UserProfile.objects.filter(
                main_character__isnull=False, main_character__character_id__in=chars_ids
            )

            character_dict = {}

            for character in users_char_ids:
                # pylint: disable=broad-exception-caught
                try:
                    character_dict[character.main_character.character_id] = {
                        "character_id": character.main_character.character_id,
                        "character_name": character.main_character.character_name,
                        "corporation_id": character.main_character.corporation_id,
                        "corporation_name": character.main_character.corporation_name,
                    }
                except AttributeError:
                    continue

            output = []
            output.append({"character": character_dict})

            return output
