from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from skillfarm.api.helpers import generate_button, generate_settings
from skillfarm.hooks import get_extension_logger
from skillfarm.models.skillfarm import CharacterSkillqueueEntry, SkillFarmAudit

logger = get_extension_logger(__name__)


def _calculate_single_progress_bar(skill: CharacterSkillqueueEntry):
    """Calculate the progress bar for a single skill"""
    totalsp = skill.level_end_sp
    start_date = skill.start_date
    finish_date = skill.finish_date

    if totalsp == 0:
        return _generate_progress_bar(0)

    current_date = timezone.now()
    total_duration = (finish_date - start_date).total_seconds()
    elapsed_duration = (current_date - start_date).total_seconds()

    if elapsed_duration > total_duration:
        progress = 100
    else:
        progress = (elapsed_duration / total_duration) * 100

    # Ensure the progress percentage is between 0 and 100
    if progress < 0:
        progress = 0
    elif progress > 100:
        progress = 100

    return _generate_progress_bar(progress)


def _calculate_progress_bar(skillqueue):
    """Calculate the progress bar for the skillqueue"""
    totalsp = 0
    trainedsp = 0

    for skill in skillqueue:
        totalsp += skill["end_sp"]
        trainedsp += skill["trained_sp"]

    if totalsp == 0:
        return _generate_progress_bar(0)

    progress = trainedsp / totalsp * 100

    return _generate_progress_bar(progress)


def _calculate_sum_progress_bar(skillqueue, skills):
    """Calculate the progress bar for the skillqueue"""
    if not skills:
        return _calculate_progress_bar(skillqueue)

    if skillqueue is None or len(skillqueue) == 0:
        return _generate_progress_bar(0)

    # Calculate the progress percentage for each skill individually
    total_progress_percent = 0
    skill_count = len(skillqueue)
    current_date = timezone.now()

    for skill in skillqueue:
        if skill["start_date"] or skill["finish_date"] == "-":
            continue

        skill_duration = (skill["finish_date"] - skill["start_date"]).total_seconds()
        skill_trained_duration = min(
            (current_date - skill["start_date"]).total_seconds(), skill_duration
        )

        skill_progress_percent = (skill_trained_duration / skill_duration) * 100

        total_progress_percent += skill_progress_percent

    # Calculate the average progress percentage
    average_progress_percent = total_progress_percent / skill_count

    # Ensure the final progress percentage is between 0 and 100
    if average_progress_percent < 0:
        average_progress_percent = 0
    elif average_progress_percent > 100:
        average_progress_percent = 100

    return _generate_progress_bar(average_progress_percent)


def _generate_progress_bar(progress) -> str:
    """Generate a progress bar"""
    progress_value = f"{progress:.0f}"
    value = int(progress_value)
    if value > 50:
        progress_value = format_html('<span class="text-white)">{}%</span>', value)
    else:
        progress_value = format_html('<span class="text-dark">{}%</span>', value)

    progressbar = format_html(
        """
        <div class="progress-outer flex-grow-1 me-2">
            <div class="progress" style="position: relative;">
                <div class="progress-bar progress-bar-warning progress-bar-striped active" role="progressbar" style="width: {}%; box-shadow: -1px 3px 5px rgba(0, 180, 231, 0.9);"></div>
                <div class="fw-bold fs-6 text-center position-absolute top-50 start-50 translate-middle">{}</div>
            </div>
        </div>
        """,
        progress,
        progress_value,
    )

    return progressbar


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
        image = "skillExtractor.png"
        title = _("Skill Extraction Ready")
        div_id = "skillfarm-skill-extractor"
        icon = "fas fa-exclamation-triangle"
        color = "red"
    elif skillqueue is True:
        image = "skillExtractorMaybe.png"
        title = _("Please check your Character a Skill should be ready for extraction")
        div_id = "skillfarm-skill-extractor-maybe"
        icon = "fas fa-question"
        color = "orange"
    else:
        return ""
    return (
        f"<img src='/static/skillfarm/images/{image}' data-tooltip-toggle='skillfarm-tooltip' class='rounded-circle' id='"
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
