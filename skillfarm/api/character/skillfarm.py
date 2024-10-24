from collections import defaultdict
from typing import List

from ninja import NinjaAPI

from django.db.models import Q
from eveuniverse.models import EveType

from allianceauth.authentication.models import UserProfile

from skillfarm.api import schema
from skillfarm.api.helpers import (
    arabic_number_to_roman,
    get_alts_queryset,
    get_character,
)
from skillfarm.hooks import get_extension_logger
from skillfarm.models.characterskill import CharacterSkill
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.models.skillfarmsetup import SkillFarmSetup
from skillfarm.models.skillqueue import CharacterSkillqueueEntry

logger = get_extension_logger(__name__)


# pylint: disable=duplicate-code
class SkillFarmApiEndpoints:
    tags = ["SkillFarm"]

    # pylint: disable=too-many-locals, too-many-statements
    def __init__(self, api: NinjaAPI):
        @api.get(
            "account/{character_id}/skillfarm/",
            response={200: List[schema.SkillFarmFilter], 403: str},
            tags=self.tags,
        )
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

            skills_queue_dict = defaultdict(list)
            skills_queue_dict_filtered = defaultdict(list)
            skills_dict = defaultdict(list)
            characters_dict = []
            output = []

            skill_names = EveType.objects.filter(
                eve_group__eve_category__id=16
            ).values_list("name", flat=True)

            # Get all Characters and related data in one query
            audit = SkillFarmAudit.objects.filter(
                character__in=characters
            ).select_related(
                "character",
            )

            for character in audit:
                character_filters = Q(
                    character__character__character_id=character.character.character_id
                )

                update_status = character.last_update_skillqueue

                # Filter Skills from Skillset
                try:
                    skillset = SkillFarmSetup.objects.get(character=character)
                except SkillFarmSetup.DoesNotExist:
                    skillset = None

                if skillset and skillset.skillset is not None:
                    character_filters &= Q(eve_type__name__in=skillset.skillset)

                    # Get all Skills for the current character if skillset is defined
                    skills = CharacterSkill.objects.filter(
                        character_filters,
                        character=character,
                    ).select_related(
                        "eve_type",
                    )

                    for entry in skills:
                        character_obj = entry.character
                        level = arabic_number_to_roman(entry.active_skill_level)

                        dict_data = {
                            "skill": f"{entry.eve_type.name} {level}",
                            "level": entry.active_skill_level,
                            "skillpoints": entry.skillpoints_in_skill,
                        }

                        skills_dict[character_obj].append(dict_data)

                # Get all Skill Queue for the current character
                skillsqueue = CharacterSkillqueueEntry.objects.filter(
                    character=character
                ).select_related(
                    "eve_type",
                )

                skillsqueue_filtered = skillsqueue.filter(character_filters)

                def process_skill_queue_entry(entry):
                    character_obj = entry.character
                    level = arabic_number_to_roman(entry.finished_level)
                    dict_data = {
                        "skill": f"{entry.eve_type.name} {level}",
                        "start_sp": entry.level_start_sp,
                        "end_sp": entry.level_end_sp,
                        "trained_sp": entry.training_start_sp,
                        "start_date": entry.start_date,
                        "finish_date": entry.finish_date,
                    }
                    return character_obj, dict_data

                if character in skills_dict:
                    skills_data = skills_dict[character]

                # Process all skill queue entries and filtered skill queue entries in one loop
                for entry in skillsqueue:
                    character_obj, dict_data = process_skill_queue_entry(entry)
                    skills_queue_dict[character_obj].append(dict_data)
                    if entry in skillsqueue_filtered:
                        skills_queue_dict_filtered[character_obj].append(dict_data)

                skills_data = skills_dict.get(character, [])
                skillqueue_data = skills_queue_dict.get(character, [])
                skillqueuefiltered_data = skills_queue_dict_filtered.get(character, [])

                characters_dict.append(
                    {
                        "character_id": character.character.character_id,
                        "character_name": character.character.character_name,
                        "corporation_id": character.character.corporation_id,
                        "corporation_name": character.character.corporation_name,
                        "active": character.active,
                        "notification": character.notification,
                        "last_update": update_status,
                        "skillset": skillset.skillset if skillset else [],
                        "skillqueuefiltered": skillqueuefiltered_data,
                        "skillqueue": skillqueue_data,
                        "skills": skills_data,
                        "is_active": any(entry.is_active for entry in skillsqueue),
                        "extraction_ready": (
                            any(entry.is_exc_ready for entry in skills)
                            if skillset
                            else False
                        ),
                    }
                )

            output.append({"skills": skill_names, "characters": characters_dict})

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
