"""App Tasks"""

import datetime

# Third Party
# pylint: disable=no-name-in-module
from celery import shared_task

from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from allianceauth.notifications import notify
from allianceauth.services.tasks import QueueOnce

from skillfarm.app_settings import (
    SKILLFARM_NOTIFICATION_COOLDOWN,
    SKILLFARM_STALE_STATUS,
)
from skillfarm.decorators import when_esi_is_available
from skillfarm.hooks import get_extension_logger
from skillfarm.models.skillfarm import (
    CharacterSkill,
    CharacterSkillqueueEntry,
    SkillFarmAudit,
)
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
    mindt = timezone.now() - datetime.timedelta(days=7)
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


# pylint: disable=unused-argument, too-many-locals
@shared_task(bind=True, base=QueueOnce)
def check_skillfarm_notifications(self, runs: int = 0):
    characters = SkillFarmAudit.objects.select_related("character").all()
    warnings = {}
    notified_characters = []

    # Create a dictionary to map main characters to their alts
    main_to_alts = {}
    for character in characters:
        main_character = (
            character.character.character_ownership.user.profile.main_character
        )
        if main_character not in main_to_alts:
            main_to_alts[main_character] = []
        main_to_alts[main_character].append(character)

    for main_character, alts in main_to_alts.items():
        msg_items = []
        for alt in alts:
            if alt.notification and not alt.is_cooldown:
                skill_names = alt.get_finished_skills()
                if skill_names:
                    # Create and Add Notification Message
                    msg = alt._generate_notification(skill_names)
                    msg_items.append(msg)
                    notified_characters.append(alt)
        if msg_items:
            # Add each message to Main Character
            warnings[main_character] = "\n".join(msg_items)
    if warnings:
        for main_character, msg in warnings.items():
            logger.debug(
                "Skilltraining has been finished for %s Skills: %s",
                main_character.character_name,
                msg,
            )
            title = _("Skillfarm Notifications")
            full_message = format_html(
                "Following Skills have finished training: \n{}", msg
            )
            notify(
                title=title,
                message=full_message,
                user=main_character.character_ownership.user,
                level="warning",
            )

            # Set notification_sent to True for all characters that were notified
            for character in notified_characters:
                character.notification_sent = True
                character.last_notification = timezone.now()
                character.save()

            runs = runs + 1

    # Reset notification for characters that have not been notified for more than a day
    for character in characters:
        if (
            character.last_notification is not None
            and character.last_notification
            < timezone.now() - datetime.timedelta(days=SKILLFARM_NOTIFICATION_COOLDOWN)
        ):
            logger.debug(
                "Notification Reseted for %s",
                character.character.character_name,
            )
            character.last_notification = None
            character.notification_sent = False
            character.save()

    logger.info("Queued %s Skillfarm Notifications", runs)
