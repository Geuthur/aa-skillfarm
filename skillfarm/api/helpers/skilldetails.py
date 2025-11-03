# Standard Library
from typing import TYPE_CHECKING

# Django
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Skillfarm
from skillfarm import __title__
from skillfarm.api.helpers.core import (
    generate_progressbar_html,
)
from skillfarm.models.skillfarmaudit import CharacterSkillqueueEntry

if TYPE_CHECKING:
    # AA Skillfarm
    from skillfarm.api.skillfarm import SkillFarmQueueSchema

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def calculate_single_progress_bar(skill: CharacterSkillqueueEntry):
    """Calculate the progress bar for a single skill"""
    totalsp = skill.level_end_sp
    start_date = skill.start_date
    finish_date = skill.finish_date

    if totalsp == 0:
        return 0

    current_date = timezone.now()
    total_duration = (finish_date - start_date).total_seconds()
    elapsed_duration = (current_date - start_date).total_seconds()

    if elapsed_duration > total_duration:
        progress = 100
    else:
        progress = (elapsed_duration / total_duration) * 100

    # Ensure the progress percentage is between 0 and 100
    progress = max(progress, 0)

    return round(progress, 2)


def _calculate_sum_progress_bar(
    skill_queue_response: list["SkillFarmQueueSchema"],
) -> str:
    """Calculate the progress bar for the skillqueue"""
    # Calculate the progress percentage for each skill individually
    total_progress_percent = 0
    skill_count = len(skill_queue_response)

    if skill_count == 0:
        return generate_progressbar_html(0)

    for skill in skill_queue_response:
        if skill.start_date and skill.finish_date == "-":
            continue
        total_progress_percent += skill.progress["value"]

    # Calculate the average progress percentage
    average_progress_percent = total_progress_percent / skill_count

    return generate_progressbar_html(average_progress_percent)
