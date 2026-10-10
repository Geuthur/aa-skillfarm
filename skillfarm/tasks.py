"""App Tasks"""

# Standard Library
import inspect
from collections.abc import Callable

# Third Party
import requests
from celery import Task, shared_task

# Django
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Min
from django.db.utils import Error
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

# AA Skillfarm
from skillfarm import __title__, app_settings
from skillfarm.helpers.discord import send_user_notification
from skillfarm.models.helpers.update_manager import CharacterUpdateSection
from skillfarm.models.prices import EveTypePrice
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)

MAX_RETRIES_DEFAULT = 3

# Default params for all tasks.
TASK_DEFAULTS = {
    "time_limit": app_settings.SKILLFARM_TASKS_TIME_LIMIT,
    "max_retries": MAX_RETRIES_DEFAULT,
}

# Default params for tasks that need bind=True and run once only.
TASK_DEFAULTS_BIND_ONCE = {**TASK_DEFAULTS, **{"bind": True, "base": QueueOnce}}

# Default params for tasks that need run once only.
TASK_DEFAULTS_ONCE = {**TASK_DEFAULTS, **{"base": QueueOnce}}

# Default params for tasks that need run once only per user and are bound to the task instance.
TASK_DEFAULTS_BIND_ONCE_USER = {
    **TASK_DEFAULTS_BIND_ONCE,
    **{"once": {"keys": ["user_id"], "graceful": True}},
}

# Default params for tasks that need run once only per character and are bound to the task instance.
TASK_DEFAULTS_BIND_ONCE_CHARACTER = {
    **TASK_DEFAULTS_BIND_ONCE,
    **{"once": {"keys": ["character_pk"], "graceful": True}},
}


@shared_task(**TASK_DEFAULTS_BIND_ONCE_USER)
def update_user_characters(
    self: Task, user_id: int, force_refresh: bool = False
) -> int:
    """Update all active skillfarm characters belonging to a specific user.

    Args:
        user_id (int): Django User ID whose characters should be updated
        force_refresh (bool): Whether to force a refresh of all sections

    Returns:
        int: Number of character updates initiated
    """
    char_pks = list(
        SkillFarmAudit.objects.filter(
            character__character_ownership__user_id=user_id, active=True
        ).values_list("pk", flat=True)
    )
    priority = (
        self.request.delivery_info.get("priority", 7)
        if hasattr(self, "request") and self.request and self.request.delivery_info
        else 7
    )
    for pk in char_pks:
        update_character.apply_async(
            args=[pk],
            kwargs={"force_refresh": force_refresh, "update_alts": False},
            priority=priority,
        )
    logger.debug("Queued %s characters for user ID %s", len(char_pks), user_id)
    return len(char_pks)


@shared_task(**TASK_DEFAULTS_ONCE)
def update_all_skillfarm(force_refresh=False):
    """Update all skillfarm characters, grouping by user."""
    # Disable characters with no owner
    SkillFarmAudit.objects.disable_characters_with_no_owner()

    # Annotate users with the oldest `last_run_finished_at` across all active skillfarm update sections
    users = (
        User.objects.filter(
            character_ownerships__character__skillfarm_character__active=True
        )
        .annotate(
            oldest_update=Min(
                "character_ownerships__character__skillfarm_character__skillfarm_update_status__last_run_finished_at"
            )
        )
        .order_by("oldest_update")
        .distinct()
    )

    queued_pks = set()
    for user in users:
        user_char_pks = list(
            SkillFarmAudit.objects.filter(
                character__character_ownership__user=user, active=True
            )
            .exclude(pk__in=queued_pks)
            .values_list("pk", flat=True)
        )
        for pk in user_char_pks:
            update_character.apply_async(
                args=[pk],
                kwargs={"force_refresh": force_refresh, "update_alts": False},
            )
            queued_pks.add(pk)

    # If there are any characters not mapped to a user, pick up remaining by oldest update
    other_chars = (
        SkillFarmAudit.objects.filter(active=True)
        .exclude(pk__in=queued_pks)
        .annotate(oldest_update=Min("skillfarm_update_status__last_run_finished_at"))
        .order_by("oldest_update")
        .distinct()
    )
    for char in other_chars:
        update_character.apply_async(
            args=[char.pk],
            kwargs={"force_refresh": force_refresh, "update_alts": False},
        )
        queued_pks.add(char.pk)

    logger.info("Queued %s Skillfarm Updates", len(queued_pks))


@shared_task(**TASK_DEFAULTS_BIND_ONCE_CHARACTER)
def update_character(
    self: Task,  # pylint: disable=unused-argument
    character_pk: int,
    force_refresh: bool = False,
    update_alts: bool = False,
) -> bool:
    """
    Update a SkillFarmAudit character by running necessary section updates directly.

    Args:
        character_pk (int): Primary key of the SkillFarmAudit character to update.
        force_refresh (bool): If True, forces a refresh of all sections.
        update_alts (bool): If True, also update other active characters of the same user.

    Returns:
        bool: True if updates were executed, False otherwise.
    """
    try:
        character = SkillFarmAudit.objects.prefetch_related(
            "skillfarm_update_status"
        ).get(pk=character_pk)
    except SkillFarmAudit.DoesNotExist:
        logger.warning("SkillFarmAudit with pk %s not found.", character_pk)
        return False

    if character.is_orphan:
        logger.info(
            "Character %s is an orphan. Skipping update.",
            character,
        )
        return False

    logger.debug(
        "Processing Audit Updates for %s", format(character.character.character_name)
    )

    if force_refresh:
        # Reset Token Error if we are forcing a refresh
        character.update_manager.reset_has_token_error()

    needs_update = character.update_manager.calc_update_needed()

    if not needs_update and not force_refresh:
        logger.info("No updates needed for %s", character.character.character_name)
    else:
        sections = CharacterUpdateSection.get_sections()
        runs = 0

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
            if task:
                task(character_pk=character.pk, force_refresh=force_refresh)
            else:
                _update_character_section(
                    character_pk=character.pk,
                    section=section,
                    force_refresh=force_refresh,
                )
            runs += 1

        logger.debug(
            "Executed %s Audit Updates for %s",
            runs,
            character.character.character_name,
        )

    if update_alts:
        user = (
            character.character.character_ownership.user
            if hasattr(character.character, "character_ownership")
            and character.character.character_ownership
            else None
        )
        if user:
            alts = (
                SkillFarmAudit.objects.filter(
                    character__character_ownership__user=user, active=True
                )
                .exclude(pk=character_pk)
                .values_list("pk", flat=True)
            )
            priority = (
                self.request.delivery_info.get("priority", 7)
                if hasattr(self, "request")
                and self.request
                and self.request.delivery_info
                else 7
            )
            for alt_pk in alts:
                update_character.apply_async(
                    args=[alt_pk],
                    kwargs={"force_refresh": force_refresh, "update_alts": False},
                    priority=priority,
                )

    return True


@shared_task(**TASK_DEFAULTS_BIND_ONCE_CHARACTER)
def update_char_skills(
    self: Task, character_pk: int, force_refresh: bool
):  # pylint: disable=unused-argument
    return _update_character_section(
        character_pk=character_pk,
        section=CharacterUpdateSection.SKILLS,
        force_refresh=force_refresh,
    )


@shared_task(**TASK_DEFAULTS_BIND_ONCE_CHARACTER)
def update_char_skillqueue(
    self: Task, character_pk: int, force_refresh: bool
):  # pylint: disable=unused-argument
    return _update_character_section(
        character_pk=character_pk,
        section=CharacterUpdateSection.SKILLQUEUE,
        force_refresh=force_refresh,
    )


def _update_character_section(character_pk: int, section: str, force_refresh: bool):
    """Update a specific section of the skillfarm audit."""
    section = CharacterUpdateSection(section)
    try:
        character = SkillFarmAudit.objects.get(pk=character_pk)
    except SkillFarmAudit.DoesNotExist:
        logger.warning("SkillFarmAudit with pk %s not found.", character_pk)
        return None

    # Reset update status for the section
    character.update_manager.reset_update_status(section)

    logger.debug(
        "Updating %s for %s", section.label, character.character.character_name
    )

    # Get the method to call for the section
    method: Callable = getattr(character, section.method_name)
    method_signature = inspect.signature(method)

    # Prepare kwargs based on whether force_refresh is accepted
    if "force_refresh" in method_signature.parameters:
        kwargs = {"force_refresh": force_refresh}
    else:
        kwargs = {}

    result = character.update_manager.perform_update_status(section, method, **kwargs)
    character.update_manager.update_section_log(section, result)
    try:
        character.update_training_and_extraction_state()
    except Exception as e:  # pylint: disable=broad-except
        logger.warning(
            "Failed to update training/extraction state for %s: %s",
            character,
            e,
        )
    return result


# pylint: disable=too-many-locals, too-many-branches
@shared_task(**TASK_DEFAULTS_ONCE)
def check_skillfarm_notifications(runs: int = 0):
    characters = SkillFarmAudit.objects.filter(active=True)
    # Create a dictionary to map main characters to their alts
    main_to_alts = {}
    for character in characters:
        try:
            main_character = (
                character.character.character_ownership.user.profile.main_character
            )
            # Raise Exception if no main character found
            if main_character is None:
                raise ObjectDoesNotExist
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
                # Do not notify if user has already reviewed/acknowledged ready extractions
                if not alt.extraction_acknowledged:
                    skill_names = []
                    skillqueue_extractions = alt.skillfarm_skillqueue.extractions(
                        alt
                    ).values_list("eve_type__name", flat=True)
                    skill_names.extend(skillqueue_extractions)

                    skills_extractions = alt.skillfarm_skills.extractions(
                        alt
                    ).values_list("eve_type__name", flat=True)
                    skill_names.extend(skills_extractions)

                    if len(skill_names) > 0:
                        # Create and Add Notification Message
                        msg = alt._generate_notification(skill_names)
                        msg_items.append(msg)

        if msg_items:
            # Add each message to Main Character
            notifiy_message = "\n".join(msg_items)
            logger.debug(
                "Skilltraining has been finished for %s Skills: %s",
                main_character.character_name,
                main_character,
            )
            title = _("Skillfarm Notifications")
            full_message = (
                f"Following Skills have finished training: \n{notifiy_message}"
            )

            send_user_notification.delay(
                user_id=main_character.character_ownership.user.id,
                title=title,
                message=full_message,
                embed_message=True,
                level="warning",
            )
            runs = runs + 1

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
