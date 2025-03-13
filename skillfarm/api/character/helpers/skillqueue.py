from skillfarm.api.character.helpers.skilldetails import (
    _calculate_single_progress_bar,
)
from skillfarm.api.helpers import (
    arabic_number_to_roman,
    generate_progressbar,
    get_skillset,
)
from skillfarm.helpers import lazy
from skillfarm.models.skillfarm import CharacterSkillqueueEntry, SkillFarmAudit


def _get_character_skillqueue(character: SkillFarmAudit) -> dict:
    """Get all Skill Queue for the current character"""
    # Get all Skill Queue for the current character
    skillset = get_skillset(character)

    skillqueue = CharacterSkillqueueEntry.objects.filter(
        character=character
    ).select_related("eve_type")

    skillqueue_dict = []
    skillqueue_filtered = []
    skillqueue_ready = False
    skillqueue_training = False

    for skill in skillqueue:
        level = arabic_number_to_roman(skill.finished_level)

        if skill.is_active:
            skillqueue_training = True

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

        if skillset is not None:
            if skill.eve_type.name in skillset:
                if skill.is_skillqueue_ready:
                    skillqueue_ready = True

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

    output = {
        "skillqueue": skillqueue_dict,
        "skillqueue_filtered": skillqueue_filtered,
        "skillqueue_ready": skillqueue_ready,
        "is_filter": lazy.get_status_icon(skillset is not None),
        "is_training": skillqueue_training,
    }

    return output


def _get_character_skillqueue_single(character: SkillFarmAudit) -> dict:
    """Get all Skill Queue for the current character"""
    # Get all Skill Queue for the current character
    skillset = get_skillset(character)

    skillqueue = CharacterSkillqueueEntry.objects.filter(
        character=character
    ).select_related("eve_type")

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

        if skillset is not None:
            if skill.eve_type.name in skillset:
                skillqueue_filtered.append(dict_data)
                continue
        skillqueue_dict.append(dict_data)

    output = {
        "skillqueue": skillqueue_dict,
        "skillqueue_filtered": skillqueue_filtered,
    }

    return output
