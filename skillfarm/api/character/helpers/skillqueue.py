# Django
from django.db import models

# AA Skillfarm
from skillfarm.api.character.helpers.skilldetails import _calculate_single_progress_bar
from skillfarm.api.helpers import (
    arabic_number_to_roman,
    generate_progressbar,
)
from skillfarm.models.skillfarmaudit import CharacterSkillqueueEntry, SkillFarmAudit


def _get_character_skillqueue(character: SkillFarmAudit) -> dict:
    """Get all Skill Queue for the current character"""
    # Get all Skill Queue for the current character
    skillqueue: models.QuerySet[CharacterSkillqueueEntry] = (
        character.skillfarm_skillqueue.filter(character=character).select_related(
            "eve_type"
        )
    )

    skillqueue_dict = []
    for skill in skillqueue:
        level = arabic_number_to_roman(skill.finished_level)

        if skill.start_date is None:
            progress = 0
        else:
            progress = _calculate_single_progress_bar(skill)

        if skill.start_date is None:
            start_date = "-"
        else:
            start_date = skill.start_date.strftime("%Y-%m-%d %H:%M")
        if skill.finish_date is None:
            end_date = "-"
        else:
            end_date = skill.finish_date.strftime("%Y-%m-%d %H:%M")

        dict_data = {
            "skill": f"{skill.eve_type.name} {level}",
            "start_sp": skill.level_start_sp,
            "end_sp": skill.level_end_sp,
            "trained_sp": skill.training_start_sp,
            "start_date": start_date,
            "finish_date": end_date,
            "progress": {"html": generate_progressbar(progress), "value": progress},
        }

        skillqueue_dict.append(dict_data)
    return skillqueue_dict


def _get_character_skillqueue_single(character: SkillFarmAudit) -> dict:
    """Get all Skill Queue for the current character"""
    # Get all Skill Queue for the current character
    skillqueue: models.QuerySet[CharacterSkillqueueEntry] = (
        character.skillfarm_skillqueue.filter(character=character).select_related(
            "eve_type"
        )
    )

    skillqueue_dict = []
    skillqueue_filtered = []

    for skill in skillqueue:
        level = arabic_number_to_roman(skill.finished_level)

        if skill.start_date is None:
            progress = 0
        else:
            progress = _calculate_single_progress_bar(skill)

        if skill.start_date is None:
            start_date = "-"
        else:
            start_date = skill.start_date.strftime("%Y-%m-%d %H:%M")
        if skill.finish_date is None:
            end_date = "-"
        else:
            end_date = skill.finish_date.strftime("%Y-%m-%d %H:%M")

        dict_data = {
            "skill": f"{skill.eve_type.name} {level}",
            "start_sp": skill.level_start_sp,
            "end_sp": skill.level_end_sp,
            "trained_sp": skill.training_start_sp,
            "start_date": start_date,
            "finish_date": end_date,
            "progress": {"html": generate_progressbar(progress), "value": progress},
        }

        if character.skillfarm_skillqueue.skill_filtered(character).exists():
            skillqueue_filtered.append(dict_data)
        else:
            skillqueue_dict.append(dict_data)

    output = {
        "skillqueue": skillqueue_dict,
        "skillqueue_filtered": skillqueue_filtered,
    }

    return output
