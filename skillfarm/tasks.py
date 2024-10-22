"""App Tasks"""

import datetime

# Third Party
# pylint: disable=no-name-in-module
from celery import shared_task

from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.notifications import notify
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
    self, character_id, force_refresh=False
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


# pylint: disable=unused-argument
@shared_task(bind=True, base=QueueOnce)
def check_skillfarm_notifications(self, runs: int = 0):
    characters = SkillFarmAudit.objects.select_related("character").all()
    owner_ids = {}
    warnings = {}

    for character in characters:
        skill_names = character.finished_skills()

        if skill_names and character.notification and not character.is_cooldown:
            character_id = character.character.character_id

            # Determine if the character_id is part of any main character's alts
            main_id = None
            for main, alts in owner_ids.items():
                if character_id in alts:
                    main_id = main
                    break

            if main_id is None:
                try:
                    owner = CharacterOwnership.objects.get(
                        character__character_id=character_id
                    )
                    main = owner.user.profile.main_character
                    alts = main.character_ownership.user.character_ownerships.all()

                    owner_ids[main.character_id] = alts.values_list(
                        "character__character_id", flat=True
                    )

                    main_id = main.character_id
                except CharacterOwnership.DoesNotExist:
                    continue
                except AttributeError:
                    continue

            msg = _("%(charname)s: %(skillname)s") % {
                "charname": character.character.character_name,
                "skillname": ", ".join(skill_names),
            }

            if main_id not in warnings:
                warnings[main_id] = []

            warnings[main_id].append(msg)
            character.notification_sent = True
            character.last_notification = timezone.now()
            character.save()

    if warnings:
        for main_id, warnings in warnings.items():
            msg = "\n".join(warnings)
            owner = CharacterOwnership.objects.get(character__character_id=main_id)
            title = _("Skillfarm Notifications")
            full_message = format_html(
                "Following Skills have finished training: \n{}", msg
            )
            notify(
                title=title,
                message=full_message,
                user=owner.user,
                level="warning",
            )
            runs = runs + 1

    logger.info("Queued %s Skillfarm Notifications", runs)
