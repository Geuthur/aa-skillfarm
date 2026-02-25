# Standard Library
from unittest.mock import patch

# Django
from django.test import override_settings

# AA Skillfarm
from skillfarm.models.prices import EveType
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.esi_stub_openapi import (
    EsiEndpoint,
    create_esi_client_stub,
)
from skillfarm.tests.testdata.utils import (
    create_skillfarm_character_from_user,
)

MODULE_PATH = "skillfarm.managers.skillqueue"

# Endpoints used in tests
TEST_ENDPOINTS = [
    EsiEndpoint("Skills", "GetCharactersCharacterIdSkillqueue", "character_id"),
]


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODULE_PATH + ".esi")
class TestSkillQueueManager(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)

        cls.eve_type = EveType.objects.get(id=1)
        cls.eve_type_2 = EveType.objects.get(id=2)

    def test_update_skillqueue(self, mock_esi):
        # given
        mock_esi.client = create_esi_client_stub(endpoints=TEST_ENDPOINTS)
        mock_esi.get_type_or_create_from_esi.side_effect = [
            (self.eve_type, True),
            (self.eve_type_2, True),
        ]
        self.skillfarm_audit.update_skillqueue(force_refresh=False)

        self.assertSetEqual(
            set(
                self.skillfarm_audit.skillfarm_skillqueue.values_list(
                    "eve_type__id", flat=True
                )
            ),
            {1, 2},
        )
        obj = self.skillfarm_audit.skillfarm_skillqueue.get(eve_type__id=1)
        self.assertEqual(obj.training_start_sp, 312345)
        self.assertEqual(obj.level_start_sp, 128000)
        self.assertEqual(obj.level_end_sp, 512000)
        self.assertEqual(obj.finished_level, 5)

        obj = self.skillfarm_audit.skillfarm_skillqueue.get(eve_type__id=2)
        self.assertEqual(obj.training_start_sp, 5000)
        self.assertEqual(obj.level_start_sp, 4000)
        self.assertEqual(obj.level_end_sp, 16000)
        self.assertEqual(obj.finished_level, 4)
