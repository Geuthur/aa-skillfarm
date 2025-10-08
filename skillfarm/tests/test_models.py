# Django
from django.test import TestCase
from django.utils import timezone

# AA Skillfarm
from skillfarm.models.skillfarmaudit import (
    CharacterSkill,
    CharacterSkillqueueEntry,
    SkillFarmAudit,
    SkillFarmSetup,
)
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import (
    create_skillfarm_character,
    create_update_status,
)

MODULE_PATH = "skillfarm.models.skillfarmaudit"


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

    def test_last_update_should_return_incomplete(self):
        """Test should return incomplete description for last_update Property"""
        self.assertEqual(
            self.audit.last_update, "One or more sections have not been updated"
        )

    def test_reset_has_token_error_should_return_false(self):
        """Test should reset has_token_error"""
        self.assertFalse(self.audit.reset_has_token_error())

    def test_reset_has_token_error_should_return_true(self):
        """Test should reset has_token_error"""
        create_update_status(
            self.audit,
            section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
            is_success=False,
            error_message="",
            has_token_error=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )
        self.assertTrue(self.audit.reset_has_token_error())
