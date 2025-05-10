# AA Skillfarm
from skillfarm.api.helpers import arabic_number_to_roman
from skillfarm.models.skillfarm import CharacterSkill, SkillFarmAudit, SkillFarmSetup


def _get_character_skills(character: SkillFarmAudit) -> dict:
    """Get all Skills for the current character"""
    try:
        skillsetup = SkillFarmSetup.objects.get(
            character=character,
            skillset__isnull=False,
        )
        skillset = skillsetup.skillset or []
    except SkillFarmSetup.DoesNotExist:
        skillset = []

    skills_dict = []

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

            skills_dict.append(dict_data)
    return skills_dict
