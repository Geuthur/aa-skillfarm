# AA Skillfarm
from skillfarm.api.helpers import arabic_number_to_roman, get_skillset
from skillfarm.models.skillfarm import CharacterSkill, SkillFarmAudit


def _get_character_skills(character: SkillFarmAudit) -> dict:
    """Get all Skills for the current character"""
    skillset = get_skillset(character)
    skills_dict = []
    extraction_ready = False

    if skillset is not None:
        skills = CharacterSkill.objects.filter(
            character=character, eve_type__name__in=skillset
        ).select_related("eve_type")

        for skill in skills:
            if skill.active_skill_level == 0:
                continue
            level = arabic_number_to_roman(skill.active_skill_level)

            dict_data = {
                "skill": f"{skill.eve_type.name} {level}",
                "level": skill.active_skill_level,
                "skillpoints": skill.skillpoints_in_skill,
            }

            if skill.is_exc_ready:
                extraction_ready = True

            skills_dict.append(dict_data)

    output = {
        "skills": skills_dict,
        "is_extraction_ready": extraction_ready,
    }

    return output
