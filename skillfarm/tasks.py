"""App Tasks"""

import datetime

import requests

# Third Party
from celery import chain, shared_task

from django.db.utils import Error
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from allianceauth.notifications import notify
from allianceauth.services.tasks import QueueOnce

from skillfarm import app_settings
from skillfarm.decorators import when_esi_is_available
from skillfarm.hooks import get_extension_logger
from skillfarm.models.prices import EveTypePrice
from skillfarm.models.skillfarm import (
    CharacterSkill,
    CharacterSkillqueueEntry,
    SkillFarmAudit,
)

logger = get_extension_logger(__name__)

MAX_RETRIES_DEFAULT = 3

# Default params for all tasks.
TASK_DEFAULTS = {
    "time_limit": app_settings.SKILLFARM_TASKS_TIME_LIMIT,
    "max_retries": MAX_RETRIES_DEFAULT,
}

# Default params for tasks that need run once only.
TASK_DEFAULTS_ONCE = {**TASK_DEFAULTS, **{"base": QueueOnce}}

_update_skillfarm_params = {
    **TASK_DEFAULTS_ONCE,
    **{"once": {"keys": ["character_id"], "graceful": True}},
}


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_all_skillfarm(runs: int = 0):
    characters = SkillFarmAudit.objects.select_related("character").all()
    for character in characters:
        update_character_skillfarm.apply_async(args=[character.character.character_id])
        runs = runs + 1
    logger.info("Queued %s Skillfarm Updates", runs)


@shared_task(**_update_skillfarm_params)
@when_esi_is_available
def update_character_skillfarm(
    character_id, force_refresh=False
):  # pylint: disable=unused-argument
    character = SkillFarmAudit.objects.get(character__character_id=character_id)

    # Settings for the Task Queue
    que = []
    skip_date = timezone.now() - datetime.timedelta(
        hours=app_settings.SKILLFARM_STALE_STATUS
    )
    mindt = timezone.now() - datetime.timedelta(days=7)
    priority = 7

    logger.debug(
        "Processing Audit Updates for %s", format(character.character.character_name)
    )
    if (character.last_update_skillqueue or mindt) <= skip_date or force_refresh:
        que.append(
            update_char_skillqueue.si(character_id, force_refresh=force_refresh).set(
                priority=priority
            )
        )

    if (character.last_update_skills or mindt) <= skip_date or force_refresh:
        que.append(
            update_char_skills.si(character_id, force_refresh=force_refresh).set(
                priority=priority
            )
        )

    chain(que).apply_async()
    logger.debug("Queued %s Tasks for %s", len(que), character.character.character_name)


@shared_task(**_update_skillfarm_params)
def update_char_skillqueue(character_id, force_refresh=False):
    character = SkillFarmAudit.objects.get(character__character_id=character_id)
    CharacterSkillqueueEntry.objects.update_or_create_esi(
        character, force_refresh=force_refresh
    )
    character.last_update_skillqueue = timezone.now()
    character.save()


@shared_task(**_update_skillfarm_params)
def update_char_skills(character_id, force_refresh=False):
    character = SkillFarmAudit.objects.get(character__character_id=character_id)
    CharacterSkill.objects.update_or_create_esi(character, force_refresh=force_refresh)
    character.last_update_skills = timezone.now()
    character.save()


@shared_task(**TASK_DEFAULTS_ONCE)
def check_skillfarm_notifications(runs: int = 0):
    characters = SkillFarmAudit.objects.filter(active=True).select_related(
        "character__character_ownership__user__profile"
    )
    notified_characters = []

    # Create a dictionary to map main characters to their alts
    main_to_alts = {}
    for character in characters:
        try:
            main_character = (
                character.character.character_ownership.user.profile.main_character
            )
        # pylint: disable=broad-exception-caught
        except Exception:
            logger.info(
                "Error getting main character from: %s - Deactivate Character",
                character,
            )
            character.active = False
            character.save()
            continue

        if main_character not in main_to_alts:
            main_to_alts[main_character] = []
        main_to_alts[main_character].append(character)

    for main_character, alts in main_to_alts.items():
        msg_items = []
        for alt in alts:
            if alt.notification:
                skill_names = alt.get_finished_skills()
                if skill_names:
                    # Create and Add Notification Message
                    msg = alt._generate_notification(skill_names)
                    msg_items.append(msg)
                    notified_characters.append(alt)
            else:
                # Reset Settings for Alts that have no notification enabled
                alt.notification_sent = False
                alt.last_notification = None
                alt.save()

        if msg_items:
            # Add each message to Main Character
            notifiy_message = "\n".join(msg_items)
            logger.debug(
                "Skilltraining has been finished for %s Skills: %s",
                main_character.character_name,
                main_character,
            )
            title = _("Skillfarm Notifications")
            full_message = format_html(
                "Following Skills have finished training: \n{}", notifiy_message
            )

            notify(
                title=title,
                message=full_message,
                user=main_character.character_ownership.user,
                level="warning",
            )
            runs = runs + 1

    if notified_characters:
        # Set notification_sent to True for all characters that were notified
        for character in notified_characters:
            character.notification_sent = True
            character.last_notification = timezone.now()
            character.save()

    logger.info("Queued %s Skillfarm Notifications", runs)


@shared_task(**TASK_DEFAULTS_ONCE)
def update_all_prices():
    prices = EveTypePrice.objects.all()
    market_data = {}

    if len(prices) == 0:
        logger.info("No Prices to update")
        return

    request = requests.get(
        "https://market.fuzzwork.co.uk/aggregates/",
        params={
            "types": ",".join([str(x) for x in prices]),
            "station": app_settings.SKILLFARM_PRICE_SOURCE_ID,
        },
    ).json()

    market_data.update(request)

    for price in prices:
        if price.eve_type.id in market_data:
            price.buy = float(market_data[price.eve_type.id]["buy"]["percentile"])
            price.sell = float(market_data[price.eve_type.id]["sell"]["percentile"])
            price.updated_at = timezone.now()

    try:
        EveTypePrice.objects.bulk_update(prices, ["buy", "sell", "updated_at"])
    except Error as e:
        logger.error("Error updating prices: %s", e)
        return

    logger.info("Skillfarm Prices updated")
