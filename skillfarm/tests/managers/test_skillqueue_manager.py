# Third Party
import pook

# AA Skillfarm
from skillfarm.models.prices import EveType
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import SkillFarmAuditFactory

MODULE_PATH = "skillfarm.managers.skillqueue"


class TestSkillQueueManager(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = SkillFarmAuditFactory(user=cls.user)

        cls.eve_type = EveType.objects.get(id=1)
        cls.eve_type_2 = EveType.objects.get(id=2)

    @pook.on
    def test_update_skillqueue(self):
        # given
        pook.get(
            f"https://esi.evetech.net/characters/{self.skillfarm_audit.character.character_id}/skillqueue",
            reply=200,
            response_json=[
                {
                    "finish_date": "2024-06-01T00:00:00Z",
                    "finished_level": 5,
                    "level_end_sp": 512000,
                    "level_start_sp": 128000,
                    "queue_position": 0,
                    "skill_id": 1,
                    "start_date": "2024-05-01T00:00:00Z",
                    "training_start_sp": 312345,
                },
                {
                    "finish_date": "2024-06-02T00:00:00Z",
                    "finished_level": 4,
                    "level_end_sp": 16000,
                    "level_start_sp": 4000,
                    "queue_position": 1,
                    "skill_id": 2,
                    "start_date": "2024-05-02T00:00:00Z",
                    "training_start_sp": 5000,
                },
            ],
        )
        # when
        self.skillfarm_audit.skillfarm_skillqueue.update_or_create_esi(
            character=self.skillfarm_audit, force_refresh=False
        )
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
