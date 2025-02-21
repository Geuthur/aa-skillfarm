from skillfarm.api.character.helpers.skilldetails import (
    _calculate_single_progress_bar,
    _generate_progress_bar,
)
from skillfarm.api.helpers import arabic_number_to_roman, get_skillset
from skillfarm.helpers import lazy
from skillfarm.models.skillfarm import CharacterSkillqueueEntry, SkillFarmAudit


def _get_character_skillqueue(character: SkillFarmAudit) -> dict:
    """Get all Skill Queue for the current character"""
    # Get all Skill Queue for the current character
    skillset = get_skillset(character)

    if skillset is None:
        skillqueue = CharacterSkillqueueEntry.objects.filter(
            character=character
        ).select_related("eve_type")
    else:
        skillqueue = CharacterSkillqueueEntry.objects.filter(
            character=character, eve_type__name__in=skillset
        ).select_related("eve_type")

    skillqueue_dict = []
    skillqueue_ready = False
    skillqueue_training = False

    for skill in skillqueue:
        level = arabic_number_to_roman(skill.finished_level)

        if skill.start_date is None:
            progress = _generate_progress_bar(0)
        else:
            progress = _calculate_single_progress_bar(skill)

        if skill.start_date is None:
            skill.start_date = "-"
        if skill.finish_date is None:
            skill.finish_date = "-"

        dict_data = {
            "skill": f"{skill.eve_type.name} {level}",
            "start_sp": skill.level_start_sp,
            "end_sp": skill.level_end_sp,
            "trained_sp": skill.training_start_sp,
            "start_date": skill.start_date,
            "finish_date": skill.finish_date,
            "progress": progress,
        }

        if skill.is_skillqueue_ready:
            skillqueue_ready = True

        if skill.is_active:
            skillqueue_training = True

        skillqueue_dict.append(dict_data)

    output = {
        "skillqueue": skillqueue_dict,
        "skillqueue_ready": skillqueue_ready,
        "is_filter": lazy.get_status_icon(skillset is not None),
        "is_training": skillqueue_training,
    }

    return output
