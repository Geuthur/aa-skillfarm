from typing import List

from ninja import NinjaAPI

from eveuniverse.models import EveType

from skillfarm.api import schema
from skillfarm.api.helpers import get_alts_queryset, get_character
from skillfarm.hooks import get_extension_logger
from skillfarm.models import SkillFarmAudit, SkillFarmSetup

logger = get_extension_logger(__name__)


# pylint: disable=duplicate-code
class SkillFarmFilterApiEndpoints:
    tags = ["SkillFarmFilter"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "account/{character_id}/filter/",
            response={200: List[schema.SkillFarmFilter], 403: str},
            tags=self.tags,
        )
        def get_character_filter(request, character_id: int):
            request_main = request.GET.get("main", False)
            perm, main = get_character(request, character_id)

            if perm is False:
                return 403, "Permission Denied"

            # Create the Ledger
            if character_id == 0 or request_main:
                characters = get_alts_queryset(main)
            else:
                characters = [main]

            output = []
            characters_dict = []

            # Get all Characters
            audit = SkillFarmAudit.objects.filter(
                character__eve_character__in=characters
            )

            skills = EveType.objects.filter(eve_group__eve_category__id=16).values_list(
                "name", flat=True
            )

            for char in audit:
                charsetup = []
                try:
                    charsetup = SkillFarmSetup.objects.get(
                        character__character__eve_character__character_id=char.character.eve_character.character_id
                    )
                    charsetup = charsetup.skillset
                except SkillFarmSetup.DoesNotExist:
                    pass

                characters_dict.append(
                    {
                        "character_id": char.character.eve_character.character_id,
                        "character_name": char.character.eve_character.character_name,
                        "corporation_id": char.character.eve_character.corporation_id,
                        "corporation_name": char.character.eve_character.corporation_name,
                        "notification": char.notification,
                        "last_update": char.last_update,
                        "skillset": charsetup,
                    }
                )

            output.append({"skills": skills, "characters": characters_dict})

            return output
