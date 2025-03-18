from django.db import models, transaction
from eveuniverse.models import EveType

from skillfarm.hooks import get_extension_logger
from skillfarm.providers import esi
from skillfarm.task_helper import (
    HTTPGatewayTimeoutError,
    NotModifiedError,
    etag_results,
)

logger = get_extension_logger(__name__)


class SkillqueueManager(models.Manager):
    def update_or_create_esi(self, character, force_refresh: bool = False):
        """Update or create skills queue for a character from ESI."""
        skillqueue = self._fetch_data_from_esi(character, force_refresh=force_refresh)

        if skillqueue is None:
            return False

        entries = []

        for entry in skillqueue:
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

        self._atomic_write(character, entries)
        return True

    def _fetch_data_from_esi(
        self, character, force_refresh: bool = False
    ) -> list[dict]:
        logger.debug("%s: Fetching skill queue from ESI", character)

        skillqueue = None
        token = character.get_token()
        try:
            skillqueue_data = esi.client.Skills.get_characters_character_id_skillqueue(
                character_id=character.character.character_id,
            )

            skillqueue = etag_results(
                skillqueue_data, token, force_refresh=force_refresh
            )
        except NotModifiedError:
            logger.debug(
                "No New Skillqueue data for: %s", character.character.character_name
            )
        except HTTPGatewayTimeoutError:
            # TODO Add retry logic?
            logger.debug(
                "Skillqueue data ESI Timeout for: %s",
                character.character.character_name,
            )

        return skillqueue

    @transaction.atomic()
    def _atomic_write(self, character, entries):
        self.filter(character=character).delete()

        if not entries:
            logger.info("%s: Skill queue is empty", character)
            return

        self.bulk_create(entries)
        logger.info("%s: Updated %s skill queue/s", character, len(entries))
