from collections import defaultdict
from typing import List

from ninja import NinjaAPI

from django.db.models import Q
from eveuniverse.models import EveType
from memberaudit.helpers import arabic_number_to_roman
from memberaudit.models import Character
from memberaudit.models.character_sections_3 import (
    CharacterSkill,
    CharacterSkillqueueEntry,
)

from allianceauth.authentication.models import UserProfile

from skillfarm.api import schema
from skillfarm.api.helpers import get_alts_queryset, get_character
from skillfarm.hooks import get_extension_logger
from skillfarm.models import SkillFarmAudit, SkillFarmSetup

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
            skills_dict = defaultdict(list)
            update_status = None
            characters_dict = []
            output = []

            skill_names = EveType.objects.filter(
                eve_group__eve_category__id=16
            ).values_list("name", flat=True)

            # Get all Characters
            audit = SkillFarmAudit.objects.filter(
                character__eve_character__in=characters
            )

            for character in audit:
                character_filters = Q(
                    character__eve_character__character_id=character.character.eve_character.character_id
                )

                # Filter Skills from Skillset
                try:
                    skillset = SkillFarmSetup.objects.get(
                        character__character__eve_character__character_id=character.character.eve_character.character_id
                    )
                except SkillFarmSetup.DoesNotExist:
                    skillset = None

                if skillset and skillset.skillset is not None:
                    character_filters &= Q(eve_type__name__in=skillset.skillset)

                    # Get all Skills for the current character if skillset is defined
                    skills = CharacterSkill.objects.select_related(
                        "character__eve_character", "eve_type"
                    ).filter(character_filters)

                    memberaudit = Character.objects.get(
                        eve_character=character.character.eve_character
                    )

                    update_status = memberaudit.update_status_as_dict()
                    update_status = update_status.get("skill_queue", None)

                    for entry in skills:
                        character_obj = entry.character.eve_character
                        level = arabic_number_to_roman(entry.active_skill_level)

                        dict_data = {
                            "skill": f"{entry.eve_type.name} {level}",
                            "level": entry.active_skill_level,
                        }

                        skills_dict[character_obj].append(dict_data)

                # Get all Skill Queue for the current character
                skillsqueue = CharacterSkillqueueEntry.objects.select_related(
                    "character__eve_character", "eve_type"
                ).filter(character_filters)

                skills_data = []

                if character.character.eve_character in skills_dict:
                    skills_data = skills_dict[character.character.eve_character]

                # Add the skillqueue to the dict
                for entry in skillsqueue:
                    character_obj = entry.character.eve_character
                    level = arabic_number_to_roman(entry.finished_level)

                    dict_data = {
                        "skill": f"{entry.eve_type.name} {level}",
                        "start_sp": entry.level_start_sp,
                        "end_sp": entry.level_end_sp,
                        "trained_sp": entry.training_start_sp,
                        "start_date": entry.start_date,
                        "finish_date": entry.finish_date,
                    }

                    skills_queue_dict[character_obj].append(dict_data)

                skillqueue_data = []

                if character.character.eve_character in skills_queue_dict:
                    skillqueue_data = skills_queue_dict[
                        character.character.eve_character
                    ]

                characters_dict.append(
                    {
                        "character_id": character.character.eve_character.character_id,
                        "character_name": character.character.eve_character.character_name,
                        "corporation_id": character.character.eve_character.corporation_id,
                        "corporation_name": character.character.eve_character.corporation_name,
                        "active": character.active,
                        "notification": character.notification,
                        "last_update": update_status.run_finished_at,
                        "skillset": skillset.skillset if skillset else [],
                        "skillqueue": skillqueue_data,
                        "skills": skills_data,
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
