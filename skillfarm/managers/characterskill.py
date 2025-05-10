# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models, transaction

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveType

# AA Skillfarm
from skillfarm import __title__
from skillfarm.app_settings import SKILLFARM_BULK_METHODS_BATCH_SIZE
from skillfarm.decorators import log_timing
from skillfarm.providers import esi
from skillfarm.task_helper import (
    etag_results,
)

if TYPE_CHECKING:
    # AA Skillfarm
    from skillfarm.models.general import UpdateSectionResult
    from skillfarm.models.skillfarm import (
        SkillFarmAudit,
    )

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class CharacterSkillManager(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, character: "SkillFarmAudit", force_refresh: bool = False
    ) -> "UpdateSectionResult":
        """Update or Create skills for a character from ESI."""
        return character.update_section_if_changed(
            section=character.UpdateSection.SKILLS,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, character: "SkillFarmAudit", force_refresh: bool = False
    ) -> dict:
        token = character.get_token()

        skills_info_data = esi.client.Skills.get_characters_character_id_skills(
            character_id=character.character.character_id,
        )

        skills_info = etag_results(skills_info_data, token, force_refresh=force_refresh)
        self._update_or_create_objs(character, skills_info)

    @transaction.atomic()
    def _update_or_create_objs(self, character: "SkillFarmAudit", objs: list):
        skills_list = {
            skill["skill_id"]: skill
            for skill in objs.get("skills", [])
            if "skill_id" in skill
        }
        skills_list = self._preload_types(skills_list)

        if skills_list is not None:
            incoming_ids = set(skills_list.keys())
            exiting_ids = set(
                self.filter(character=character).values_list("eve_type_id", flat=True)
            )

            obsolete_ids = exiting_ids.difference(incoming_ids)
            if obsolete_ids:
                logger.debug(
                    "%s: Deleting %s obsolete skill/s", character, len(obsolete_ids)
                )
                self.filter(character=character, eve_type_id__in=obsolete_ids).delete()

            create_ids = incoming_ids.difference(exiting_ids)
            if create_ids:
                self._create_from_dict(
                    character=character, skills_list=skills_list, create_ids=create_ids
                )

            update_ids = incoming_ids.intersection(exiting_ids)
            if update_ids:
                self._update_from_dict(
                    character=character, skills_list=skills_list, update_ids=update_ids
                )

    def _preload_types(self, objs: list):
        skills_list = {
            skill["skill_id"]: skill
            for skill in objs.get("skills", [])
            if "skill_id" in skill
        }
        if skills_list:
            incoming_ids = set(skills_list.keys())
            existing_ids = set(self.values_list("eve_type_id", flat=True))
            new_ids = incoming_ids.difference(existing_ids)
            EveType.objects.bulk_get_or_create_esi(ids=list(new_ids))
            return skills_list
        return None

    def _create_from_dict(self, character, skills_list: dict, create_ids: set):
        logger.debug("%s: Storing %s new skills", character, len(create_ids))
        skills = [
            self.model(
                name=character.name,
                character=character,
                eve_type=EveType.objects.get(id=skill_info.get("skill_id")),
                active_skill_level=skill_info.get("active_skill_level"),
                skillpoints_in_skill=skill_info.get("skillpoints_in_skill"),
                trained_skill_level=skill_info.get("trained_skill_level"),
            )
            for skill_id, skill_info in skills_list.items()
            if skill_id in create_ids
        ]
        self.bulk_create(skills, batch_size=SKILLFARM_BULK_METHODS_BATCH_SIZE)

    def _update_from_dict(self, character, skills_list: dict, update_ids: set):
        logger.debug("%s: Updating %s skills", character, len(update_ids))
        update_pks = list(
            self.filter(character=character, eve_type_id__in=update_ids).values_list(
                "pk", flat=True
            )
        )
        skills = self.in_bulk(update_pks)
        for skill in skills.values():
            skill_info = skills_list.get(skill.eve_type_id)
            if skill_info:
                skill.active_skill_level = skill_info.get("active_skill_level")
                skill.skillpoints_in_skill = skill_info.get("skillpoints_in_skill")
                skill.trained_skill_level = skill_info.get("trained_skill_level")

        self.bulk_update(
            skills.values(),
            fields=[
                "active_skill_level",
                "skillpoints_in_skill",
                "trained_skill_level",
            ],
            batch_size=SKILLFARM_BULK_METHODS_BATCH_SIZE,
        )
