from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from skillfarm.api.helpers import (
    generate_button,
    generate_progressbar,
    generate_settings,
)
from skillfarm.hooks import get_extension_logger
from skillfarm.models.skillfarm import CharacterSkillqueueEntry, SkillFarmAudit

logger = get_extension_logger(__name__)


def _calculate_single_progress_bar(skill: CharacterSkillqueueEntry):
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


def _calculate_sum_progress_bar(skillqueue: dict):
    """Calculate the progress bar for the skillqueue"""
    # Calculate the progress percentage for each skill individually
    total_progress_percent = 0
    skill_count = len(skillqueue)

    if skill_count == 0:
        return generate_progressbar(0)

    for skill in skillqueue:
        if skill["start_date"] and skill["finish_date"] == "-":
            continue
        total_progress_percent += skill["progress"]["value"]

    # Calculate the average progress percentage
    average_progress_percent = total_progress_percent / skill_count

    return generate_progressbar(average_progress_percent)


# pylint: disable=too-many-arguments, too-many-positional-arguments
def generate_action_settings(
    character: SkillFarmAudit,
    title,
    icon,
    color,
    modal,
    viewname,
    request,
    text: str = "",
):
    """Generate a settings dict for the skillfarm"""
    url = reverse(
        viewname=viewname,
        kwargs={
            "character_id": character.character.character_id,
        },
    )
    settings = generate_settings(
        title=title,
        icon=icon,
        color=color,
        text=text,
        modal=modal,
        action=url,
        ajax="action",
    )
    return generate_button(
        "skillfarm/partials/forms/button.html",
        character,
        settings,
        request,
    )


def _skillfarm_actions(character: SkillFarmAudit, perms, request):
    """Generate the skillfarm actions buttons for Skill Details"""
    actions = []
    if perms:
        actions.append(
            generate_action_settings(
                character=character,
                title=_("Toggle Alarm"),
                icon="fas fa-bullhorn",
                color="primary",
                modal="skillfarm-confirm",
                viewname="skillfarm:switch_alarm",
                request=request,
                text=_("Are you sure you want to toggle the alarm for {}?").format(
                    character.character.character_name
                ),
            )
        )
        actions.append(
            generate_action_settings(
                character=character,
                title=_("Edit Skillset"),
                icon="fas fa-pencil",
                color="warning",
                modal="skillfarm-skillset",
                viewname="skillfarm:skillset",
                request=request,
            )
        )
        actions.append(
            generate_action_settings(
                character=character,
                title=_("Delete Character"),
                icon="fas fa-trash",
                color="danger",
                modal="skillfarm-confirm",
                viewname="skillfarm:delete_character",
                request=request,
                text=_("Are you sure you want to delete {}?").format(
                    character.character.character_name
                ),
            )
        )

    actions_html = format_html("".join(actions))
    return format_html('<div class="d-flex justify-content-end">{}</div>', actions_html)


def _get_skillinfo_actions(character: SkillFarmAudit, request):
    """Get the skillinfo actions for the skillfarm"""
    settings = generate_settings(
        title=_("Skillinfo"),
        icon="fas fa-info",
        color="primary",
        text="",
        modal="modalViewSkillContainer",
        action=reverse(
            viewname="skillfarm:api:get_skillinfo_details",
            kwargs={
                "character_id": character.character.character_id,
            },
        ),
        ajax="ajax_skillview",
    )
    return generate_button(
        "skillfarm/partials/forms/button.html",
        character,
        settings,
        request,
    )


def _get_extraction_icon(skills, skillqueue) -> str:
    """Get the extraction icon"""
    if skills is True:
        title = _("Skill Extraction Ready")
        div_id = "skillfarm-skill-extractor"
        icon = "fas fa-exclamation-triangle"
        color = "red"
    elif skillqueue is True:
        title = _("Please check your Character a Skill should be ready for extraction")
        div_id = "skillfarm-skill-extractor-maybe"
        icon = "fas fa-question"
        color = "orange"
    else:
        return ""
    return (
        "<img src='/static/skillfarm/images/skillExtractor.png' data-tooltip-toggle='skillfarm-tooltip' class='rounded-circle' id='"
        + div_id
        + "'style='width: 32px'>"
        + f"<i class='{icon}' style='margin-left: 5px; color: {color}' title='"
        + title
        + "' data-tooltip-toggle='skillfarm-tooltip'></i>"
    )


def _get_notification_icon(status: bool) -> str:
    """Get the notification icon"""
    html = "<i class='fa-solid fa-bullhorn' style='margin-left: 5px; color:"
    if status:
        html += (
            "green' title='"
            + _("Notification Activated")
            + "' data-tooltip-toggle='skillfarm-tooltip'></i>"
        )
    else:
        html += (
            "gray' title='"
            + _("Notification Deactivated")
            + "' data-tooltip-toggle='skillfarm-tooltip'></i>"
        )
    return html
