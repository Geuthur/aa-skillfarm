# Standard Library
from typing import TYPE_CHECKING

# Django
from django.core.exceptions import ObjectDoesNotExist
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

if TYPE_CHECKING:
    # Alliance Auth
    from esi.stubs import CharactersCharacterIdSkillsGet
    from esi.stubs import CharactersCharacterIdSkillsGet_SkillsItem as SkillItems

    # AA Skillfarm
    from skillfarm.models.general import UpdateSectionResult
    from skillfarm.models.skillfarmaudit import (
        SkillFarmAudit,
    )

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class SkillManagerQuerySet(models.QuerySet):
    # pylint: disable=duplicate-code
    def extractions(self, character: "SkillFarmAudit") -> bool:
        """Return extraction ready skills from a training queue."""
        try:
            skillsetup = character.skillfarm_setup
            if not skillsetup or not skillsetup.skillset:
                skillset = []
            else:
                skillset = skillsetup.skillset
        except ObjectDoesNotExist:
            skillset = []

        extraction = self.filter(
            trained_skill_level=5,
            eve_type__name__in=skillset,
        )

        return extraction

    # pylint: disable=duplicate-code
    def skill_filtered(self, character: "SkillFarmAudit") -> bool:
        """Return filtered skills from a training queue."""
        try:
            skillsetup = character.skillfarm_setup
            if not skillsetup or not skillsetup.skillset:
                skillset = []
            else:
                skillset = skillsetup.skillset
        except ObjectDoesNotExist:
            skillset = []

        skills = self.filter(
            eve_type__name__in=skillset,
        )
        return skills


class SkillManagerBase(models.Manager):
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

        # Make the ESI request
        character_skills = esi.client.Skills.GetCharactersCharacterIdSkills(
            character_id=character.character.character_id,
            token=token,
        )
        character_skills_items = character_skills.results(force_refresh=force_refresh)

        self._update_or_create_objs(
            character=character, character_skills_items=character_skills_items
        )

    @transaction.atomic()
    def _update_or_create_objs(
        self,
        character: "SkillFarmAudit",
        character_skills_items: list["CharactersCharacterIdSkillsGet"],
    ) -> None:
        """Update or Create skill entries from objs data."""
        for character_skills in character_skills_items:
            skills_list = self._preload_types(character_skills)
            if skills_list is not None:
                incoming_ids = set(skills_list)
                existing_ids = set(
                    self.filter(character=character).values_list(
                        "eve_type_id", flat=True
                    )
                )

                obsolete_ids = existing_ids.difference(incoming_ids)
                if obsolete_ids:
                    logger.debug(
                        "%s: Deleting %s obsolete skill/s", character, len(obsolete_ids)
                    )
                    self.filter(
                        character=character, eve_type_id__in=obsolete_ids
                    ).delete()

                create_ids = incoming_ids.difference(existing_ids)
                if create_ids:
                    self._create_from_list(
                        character=character,
                        skills_list=character_skills.skills,
                        create_ids=create_ids,
                    )

                update_ids = incoming_ids.intersection(existing_ids)
                if update_ids:
                    self._update_from_list(
                        character=character,
                        skills_list=character_skills.skills,
                        update_ids=update_ids,
                    )

    def _preload_types(
        self, character_skills_items: "CharactersCharacterIdSkillsGet"
    ) -> list[int] | None:
        """Preload EveType objects from a list of skills."""
        skills_list = [skill.skill_id for skill in character_skills_items.skills]
        if skills_list:
            incoming_ids = set(skills_list)
            existing_ids = set(self.values_list("eve_type_id", flat=True))
            new_ids = incoming_ids.difference(existing_ids)
            EveType.objects.bulk_get_or_create_esi(ids=list(new_ids))
            return skills_list
        return None

    def _create_from_list(
        self,
        character: "SkillFarmAudit",
        skills_list: list["SkillItems"],
        create_ids: set,
    ):
        logger.debug("%s: Storing %s new skills", character, len(create_ids))
        skills = [
            self.model(
                name=character.name,
                character=character,
                eve_type=EveType.objects.get(id=skill.skill_id),
                active_skill_level=skill.active_skill_level,
                skillpoints_in_skill=skill.skillpoints_in_skill,
                trained_skill_level=skill.trained_skill_level,
            )
            for skill in skills_list
            if skill.skill_id in create_ids
        ]
        self.bulk_create(skills, batch_size=SKILLFARM_BULK_METHODS_BATCH_SIZE)

    def _update_from_list(
        self,
        character,
        skills_list: list["SkillItems"],
        update_ids: set,
    ):
        logger.debug("%s: Updating %s skills", character, len(update_ids))
        update_pks = list(
            self.filter(character=character, eve_type_id__in=update_ids).values_list(
                "pk", flat=True
            )
        )
        skills = self.in_bulk(update_pks)
        skills_dict = {s.skill_id: s for s in skills_list}
        for skill in skills.values():
            if skill.eve_type_id in skills_dict:
                skill_ctx = skills_dict[skill.eve_type_id]
                skill.active_skill_level = skill_ctx.active_skill_level
                skill.skillpoints_in_skill = skill_ctx.skillpoints_in_skill
                skill.trained_skill_level = skill_ctx.trained_skill_level

        self.bulk_update(
            skills.values(),
            fields=[
                "active_skill_level",
                "skillpoints_in_skill",
                "trained_skill_level",
            ],
            batch_size=SKILLFARM_BULK_METHODS_BATCH_SIZE,
        )


SkillManager = SkillManagerBase.from_queryset(SkillManagerQuerySet)
