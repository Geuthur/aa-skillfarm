"""App Tasks"""

# Third Party
# pylint: disable=no-name-in-module
from celery import shared_task

from django.utils.translation import gettext_lazy as _

from skillfarm.decorators import when_esi_is_available
from skillfarm.hooks import get_extension_logger
from skillfarm.models import SkillFarmAudit
from skillfarm.task_helper import update_character_skillfarm

logger = get_extension_logger(__name__)


@shared_task
@when_esi_is_available
def update_all_skillfarm(runs: int = 0):
    characters = SkillFarmAudit.objects.select_related("character").all()
    for char in characters:
        update_character_skillfarm.apply_async(args=[char.character.character_id])
        runs = runs + 1
    logger.info("Queued %s Skillfarm Updates", runs)
