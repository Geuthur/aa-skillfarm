# Django
from django.db import models, transaction
from eveuniverse.models import EveType

from skillfarm.app_settings import SKILLFARM_BULK_METHODS_BATCH_SIZE
from skillfarm.hooks import get_extension_logger
from skillfarm.providers import esi
from skillfarm.task_helper import NotModifiedError, etag_results

logger = get_extension_logger(__name__)


class CharacterSkillManager(models.Manager):
    def update_or_create_esi(self, character, force_refresh: bool = False):
        """Update or create skills for a character from ESI."""
        skills = self._fetch_data_from_esi(character, force_refresh=force_refresh)

        if not skills:
            return False

        skills_list = {
            skill["skill_id"]: skill
            for skill in skills.get("skills", [])
            if "skill_id" in skill
        }
        self._preload_types(skills_list)

        self._atomic_write(character, skills_list)
        return True

    def _preload_types(self, skills_list: dict):
        if skills_list:
            incoming_ids = set(skills_list.keys())
            existing_ids = set(self.values_list("eve_type_id", flat=True))
            new_ids = incoming_ids.difference(existing_ids)
            EveType.objects.bulk_get_or_create_esi(ids=list(new_ids))

    def _fetch_data_from_esi(self, character, force_refresh: bool = False) -> dict:
        logger.debug("%s: Fetching skills from ESI", character)

        skills_info = []
        token = character.get_token()
        try:
            skills_info_data = esi.client.Skills.get_characters_character_id_skills(
                character_id=character.character.character_id,
            )

            skills_info = etag_results(
                skills_info_data, token, force_refresh=force_refresh
            )
        except NotModifiedError:
            logger.debug(
                "No New Skillque data for: %s", character.character.character_name
            )

        return skills_info

    @transaction.atomic()
    def _atomic_write(self, character, skills_list: dict):
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

        create_ids = None
        update_ids = None

        if skills_list:
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

        if not obsolete_ids and not create_ids and not update_ids:
            logger.debug("%s: No changes in skills", character)

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
