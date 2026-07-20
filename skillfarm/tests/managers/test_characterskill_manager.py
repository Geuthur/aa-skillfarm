# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock

# Third Party
import pook

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import SkillFarmAuditFactory

MODULE_PATH = "skillfarm.managers.characterskill"


class TestCharacterSkillManager(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.skillfarm_audit = SkillFarmAuditFactory(user=cls.user)
        cls.token = cls.user.token_set.first()
        cls.skillfarm_audit.get_token = MagicMock(return_value=cls.token)

    @pook.on
    def test_update_skills(self):
        # given

        pook.get(
            f"https://esi.evetech.net/characters/{self.skillfarm_audit.character.character_id}/skills",
            reply=HTTPStatus.OK,
            response_json={
                "skills": [
                    {
                        "skill_id": 1,
                        "trained_skill_level": 5,
                        "active_skill_level": 4,
                        "skillpoints_in_skill": 128000,
                    },
                    {
                        "skill_id": 2,
                        "trained_skill_level": 4,
                        "active_skill_level": 2,
                        "skillpoints_in_skill": 4000,
                    },
                ],
                "total_sp": 75000000,
                "unallocated_sp": 250000,
            },
        )
        self.skillfarm_audit.skillfarm_skills.update_or_create_esi(
            character=self.skillfarm_audit, force_refresh=False
        )

        self.assertSetEqual(
            set(
                self.skillfarm_audit.skillfarm_skills.all().values_list(
                    "eve_type__id", flat=True
                )
            ),
            {1, 2},
        )
        obj = self.skillfarm_audit.skillfarm_skills.get(eve_type__id=1)
        self.assertEqual(obj.active_skill_level, 4)
        self.assertEqual(obj.skillpoints_in_skill, 128000)
        self.assertEqual(obj.trained_skill_level, 5)

        obj = self.skillfarm_audit.skillfarm_skills.get(eve_type__id=2)
        self.assertEqual(obj.active_skill_level, 2)
        self.assertEqual(obj.skillpoints_in_skill, 4000)
        self.assertEqual(obj.trained_skill_level, 4)
