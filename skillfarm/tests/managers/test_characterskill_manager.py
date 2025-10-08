# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings

# Alliance Auth (External Libs)
from app_utils.testing import NoSocketsTestCase

# AA Skillfarm
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.esi_stub import esi_client_stub_openapi
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import (
    create_skillfarm_character,
)

MODULE_PATH = "skillfarm.managers.characterskill"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
@patch(MODULE_PATH + ".EveType.objects.bulk_get_or_create_esi", spec=True)
class TestCharacterSkillManager(NoSocketsTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.audit = create_skillfarm_character(1001)

    def test_update_skills(self, _, mock_esi):
        # given
        mock_esi.client = esi_client_stub_openapi
        self.audit.update_skills(force_refresh=False)

        self.assertSetEqual(
            set(
                self.audit.skillfarm_skills.all().values_list("eve_type__id", flat=True)
            ),
            {1, 2},
        )
        obj = self.audit.skillfarm_skills.get(eve_type__id=1)
        self.assertEqual(obj.active_skill_level, 4)
        self.assertEqual(obj.skillpoints_in_skill, 128000)
        self.assertEqual(obj.trained_skill_level, 5)

        obj = self.audit.skillfarm_skills.get(eve_type__id=2)
        self.assertEqual(obj.active_skill_level, 2)
        self.assertEqual(obj.skillpoints_in_skill, 4000)
        self.assertEqual(obj.trained_skill_level, 4)
