"""App Tasks"""

import datetime

# Third Party
# pylint: disable=no-name-in-module
from celery import shared_task

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from allianceauth.services.tasks import QueueOnce

from skillfarm.app_settings import SKILLFARM_STALE_STATUS
from skillfarm.decorators import when_esi_is_available
from skillfarm.hooks import get_extension_logger
from skillfarm.models import CharacterSkill, CharacterSkillqueueEntry, SkillFarmAudit
from skillfarm.task_helper import enqueue_next_task, no_fail_chain

logger = get_extension_logger(__name__)


@shared_task
@when_esi_is_available
def update_all_skillfarm(runs: int = 0):
    characters = SkillFarmAudit.objects.select_related("character").all()
    for character in characters:
        update_character_skillfarm.apply_async(args=[character.character.character_id])
        runs = runs + 1
    logger.info("Queued %s Skillfarm Updates", runs)


@shared_task(bind=True, base=QueueOnce)
def update_character_skillfarm(
    self, character_id, force_refresh=True
):  # pylint: disable=unused-argument
    character = SkillFarmAudit.objects.get(character__character_id=character_id)
    skip_date = timezone.now() - datetime.timedelta(hours=SKILLFARM_STALE_STATUS)
    que = []
    mindt = timezone.now() - datetime.timedelta(days=90)
    logger.debug(
        "Processing Audit Updates for %s", format(character.character.character_name)
    )
    if (character.last_update_skillqueue or mindt) <= skip_date or force_refresh:
        que.append(update_char_skillqueue.si(character_id, force_refresh=force_refresh))

    if (character.last_update_skills or mindt) <= skip_date or force_refresh:
        que.append(update_char_skills.si(character_id, force_refresh=force_refresh))

    enqueue_next_task(que)

    logger.debug("Queued %s Tasks for %s", len(que), character.character.character_name)


@shared_task(
    bind=True,
    base=QueueOnce,
    once={"graceful": False, "keys": ["character_id"]},
    name="tasks.update_char_skillqueue",
)
@no_fail_chain
def update_char_skillqueue(
    self, character_id, force_refresh=False, chain=[]
):  # pylint: disable=unused-argument, dangerous-default-value
    character = SkillFarmAudit.objects.get(character__character_id=character_id)
    CharacterSkillqueueEntry.objects.update_or_create_esi(
        character, force_refresh=force_refresh
    )
    character.last_update_skillqueue = timezone.now()
    character.save()


@shared_task(
    bind=True,
    base=QueueOnce,
    once={"graceful": False, "keys": ["character_id"]},
    name="tasks.update_char_skills",
)
@no_fail_chain
def update_char_skills(
    self, character_id, force_refresh=False, chain=[]
):  # pylint: disable=unused-argument, dangerous-default-value
    character = SkillFarmAudit.objects.get(character__character_id=character_id)
    CharacterSkill.objects.update_or_create_esi(character, force_refresh=force_refresh)
    character.last_update_skills = timezone.now()
    character.save()
