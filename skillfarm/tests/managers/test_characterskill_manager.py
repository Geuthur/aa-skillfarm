# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)
from skillfarm.tests.testdata.utils import (
    create_skillfarm_character_from_user,
)

MODULE_PATH = "skillfarm.managers.characterskill"

# Endpoints used in tests
TEST_ENDPOINTS = [
    EsiEndpoint("Skills", "GetCharactersCharacterIdSkills", "character_id"),
]


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
class TestCharacterSkillManager(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)

    def test_update_skills(self, mock_esi):
        # given

        mock_esi.client = create_esi_client_stub(endpoints=TEST_ENDPOINTS)
        self.skillfarm_audit.update_skills(force_refresh=False)

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
