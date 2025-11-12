"""App Tasks"""

# Standard Library
import inspect
from collections.abc import Callable

# Third Party
import requests
from celery import chain, shared_task

# Django
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import Error
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Skillfarm
from skillfarm import __title__, app_settings
from skillfarm.decorators import when_esi_is_available
from skillfarm.helpers.discord import send_user_notification
from skillfarm.models.prices import EveTypePrice
from skillfarm.models.skillfarmaudit import (
    SkillFarmAudit,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

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
    **{"once": {"keys": ["character_pk", "force_refresh"], "graceful": True}},
}


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_all_skillfarm(runs: int = 0, force_refresh=False):
    """Update all skillfarm characters."""
    SkillFarmAudit.objects.disable_characters_with_no_owner()
    characters = SkillFarmAudit.objects.select_related("character").filter(active=True)
    for character in characters:
        update_character.apply_async(
            args=[character.pk], kwargs={"force_refresh": force_refresh}
        )
        runs = runs + 1
    logger.info("Queued %s Skillfarm Updates", runs)


@shared_task(**TASK_DEFAULTS_ONCE)
@when_esi_is_available
def update_character(character_pk: int, force_refresh=False):
    character = SkillFarmAudit.objects.prefetch_related("skillfarm_update_status").get(
        pk=character_pk
    )

    que = []
    priority = 7

    logger.debug(
        "Processing Audit Updates for %s", format(character.character.character_name)
    )

    if force_refresh:
        # Reset Token Error if we are forcing a refresh
        character.reset_has_token_error()

    needs_update = character.calc_update_needed()

    if not needs_update and not force_refresh:
        logger.info("No updates needed for %s", character.character.character_name)
        return

    sections = character.UpdateSection.get_sections()

    for section in sections:
        # Skip sections that are not in the needs_update list
        if not force_refresh and not needs_update.for_section(section):
            logger.debug(
                "No updates needed for %s (%s)",
                character.character.character_name,
                section,
            )
            continue

        task_name = f"update_char_{section}"
        task = globals().get(task_name)
        que.append(
            task.si(character.pk, force_refresh=force_refresh).set(priority=priority)
        )

    chain(que).apply_async()
    logger.debug(
        "Queued %s Audit Updates for %s",
        len(que),
        character.character.character_name,
    )


@shared_task(**_update_skillfarm_params)
def update_char_skills(character_pk: int, force_refresh: bool):
    return _update_character_section(
        character_pk,
        section=SkillFarmAudit.UpdateSection.SKILLS,
        force_refresh=force_refresh,
    )


@shared_task(**_update_skillfarm_params)
def update_char_skillqueue(character_pk: int, force_refresh: bool):
    return _update_character_section(
        character_pk,
        section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
        force_refresh=force_refresh,
    )


def _update_character_section(character_pk: int, section: str, force_refresh: bool):
    """Update a specific section of the skillfarm audit."""
    section = SkillFarmAudit.UpdateSection(section)
    character = SkillFarmAudit.objects.get(pk=character_pk)
    logger.debug(
        "Updating %s for %s", section.label, character.character.character_name
    )

    character.reset_update_status(section)

    method: Callable = getattr(character, section.method_name)
    method_signature = inspect.signature(method)

    if "force_refresh" in method_signature.parameters:
        kwargs = {"force_refresh": force_refresh}
    else:
        kwargs = {}
    result = character.perform_update_status(section, method, **kwargs)
    character.update_section_log(section, result)


# pylint: disable=too-many-locals
@shared_task(**TASK_DEFAULTS_ONCE)
def check_skillfarm_notifications(runs: int = 0):
    characters = SkillFarmAudit.objects.filter(active=True)
    notified_characters = []

    # Create a dictionary to map main characters to their alts
    main_to_alts = {}
    for character in characters:
        try:
            main_character = (
                character.character.character_ownership.user.profile.main_character
            )
        except ObjectDoesNotExist:
            logger.warning(
                "Main Character not found for %s, skipping notification",
                character.character.character_name,
            )
            continue

        if main_character not in main_to_alts:
            main_to_alts[main_character] = []
        main_to_alts[main_character].append(character)

    for main_character, alts in main_to_alts.items():
        msg_items = []
        for alt in alts:
            alt: SkillFarmAudit

            if alt.notification:
                skill_names = []
                skillqueue_extractions = alt.skillfarm_skillqueue.extractions(
                    alt
                ).values_list("eve_type__name", flat=True)
                skill_names.extend(skillqueue_extractions)

                skills_extractions = alt.skillfarm_skills.extractions(alt).values_list(
                    "eve_type__name", flat=True
                )
                skill_names.extend(skills_extractions)

                if len(skill_names) > 0:
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

            send_user_notification.delay(
                user_id=main_character.character_ownership.user.id,
                title=title,
                message=full_message,
                embed_message=True,
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
            "types": ",".join([str(x.eve_type.id) for x in prices]),
            "station": app_settings.SKILLFARM_PRICE_SOURCE_ID,
        },
    ).json()

    market_data.update(request)

    for price in prices:
        key = str(price.eve_type.id)
        if key in market_data:
            logger.info(
                "Updating Price for %s (%s)",
                price.eve_type.name,
                price.eve_type.id,
            )
            price.buy = float(market_data[key]["buy"]["percentile"])
            price.sell = float(market_data[key]["sell"]["percentile"])
            price.updated_at = timezone.now()

    try:
        EveTypePrice.objects.bulk_update(prices, ["buy", "sell", "updated_at"])
    except Error as e:
        logger.error("Error updating prices: %s", e)
        return

    logger.info("Skillfarm Prices updated")
