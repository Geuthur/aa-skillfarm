# Django
from django.test import TestCase
from django.utils import timezone

# Alliance Auth (External Libs)
from app_utils.testing import create_user_from_evecharacter
from eveuniverse.models import EveType

# AA Skillfarm
from skillfarm.models.skillfarm import (
    CharacterSkill,
    CharacterSkillqueueEntry,
    SkillFarmAudit,
    SkillFarmSetup,
)
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import create_skillfarm_character

MODULE_PATH = "skillfarm.models.skillfarm"


class TestSkillfarmModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.audit = create_skillfarm_character(1001)

    def test_should_return_string_audit(self):
        """Test should return the Audit Character Data"""
        self.assertEqual(str(self.audit), "Gneuten - Active: True - Status: incomplete")

    def test_should_return_esi_scopes(self):
        """Test should return the ESI Scopes for Skillfarm"""
        self.assertEqual(
            self.audit.get_esi_scopes(),
            ["esi-skills.read_skills.v1", "esi-skills.read_skillqueue.v1"],
        )

    def test_is_cooldown_should_return_false(self):
        """Test should return False for is_cooldown Property"""
        self.assertFalse(self.audit.is_cooldown)

    def test_is_cooldown_should_return_true(self):
        """Test should return True for is_cooldown Property"""
        self.audit.last_notification = timezone.now()
        self.assertTrue(self.audit.is_cooldown)
