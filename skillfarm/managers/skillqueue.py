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


class SkillqueueManager(models.Manager):
    @log_timing(logger)
    def update_or_create_esi(
        self, character: "SkillFarmAudit", force_refresh: bool = False
    ) -> "UpdateSectionResult":
        """Update or Create skills for a character from ESI."""
        return character.update_section_if_changed(
            section=character.UpdateSection.SKILLQUEUE,
            fetch_func=self._fetch_esi_data,
            force_refresh=force_refresh,
        )

    def _fetch_esi_data(
        self, character: "SkillFarmAudit", force_refresh: bool = False
    ) -> dict:
        """Fetch Skillqueue entries from ESI data."""
        token = character.get_token()

        skillqueue_data = esi.client.Skills.get_characters_character_id_skillqueue(
            character_id=character.character.character_id,
        )

        skillqueue = etag_results(skillqueue_data, token, force_refresh=force_refresh)
        self._update_or_create_objs(character, skillqueue)

    @transaction.atomic()
    def _update_or_create_objs(self, character: "SkillFarmAudit", objs: list):
        """Update or Create skill queue entries from objs data."""
        entries = []

        for entry in objs:
            eve_type_instance, _ = EveType.objects.get_or_create_esi(
                id=entry.get("skill_id")
            )
            entries.append(
                self.model(
                    name=character.name,
                    character=character,
                    eve_type=eve_type_instance,
                    finish_date=entry.get("finish_date"),
                    finished_level=entry.get("finished_level"),
                    level_end_sp=entry.get("level_end_sp"),
                    level_start_sp=entry.get("level_start_sp"),
                    queue_position=entry.get("queue_position"),
                    start_date=entry.get("start_date"),
                    training_start_sp=entry.get("training_start_sp"),
                )
            )

        self.filter(character=character).delete()

        if len(entries) > 0:
            self.bulk_create(entries)
