# Django
from django.test import TestCase
from django.utils import timezone

# AA Skillfarm
from skillfarm.models.skillfarmaudit import (
    SkillFarmAudit,
)
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.integrations.allianceauth import load_allianceauth
from skillfarm.tests.testdata.utils import (
    create_skillfarm_character_from_user,
    create_update_status,
)

MODULE_PATH = "skillfarm.models.skillfarmaudit"


class TestSkillfarmModel(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create SkillfarmAudit instance
        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)

    def test_should_return_string_audit(self):
        """
        Test should return string representation of SkillFarmAudit.
        """
        self.assertEqual(
            str(self.skillfarm_audit), "Gneuten - Active: True - Status: incomplete"
        )

    def test_should_return_esi_scopes(self):
        """
        Test should return ESI scopes required for SkillFarmAudit.
        """
        self.assertEqual(
            self.skillfarm_audit.get_esi_scopes(),
            ["esi-skills.read_skills.v1", "esi-skills.read_skillqueue.v1"],
        )

    def test_is_cooldown_should_return_false(self):
        """
        Test should return False for is_cooldown Property.
        """
        self.assertFalse(self.skillfarm_audit.is_cooldown)

    def test_is_cooldown_should_return_true(self):
        """
        Test should return True for is_cooldown Property.
        """
        self.skillfarm_audit.last_notification = timezone.now()
        self.assertTrue(self.skillfarm_audit.is_cooldown)

    def test_last_update_should_return_incomplete(self):
        """
        Test should return incomplete for last_update Property.
        """
        self.assertEqual(
            self.skillfarm_audit.last_update,
            "One or more sections have not been updated",
        )

    def test_reset_has_token_error_should_return_false(self):
        """
        Test should not reset has_token_error.
        """
        self.assertFalse(self.skillfarm_audit.reset_has_token_error())

    def test_reset_has_token_error_should_return_true(self):
        """
        Test should reset has_token_error.
        """
        create_update_status(
            self.skillfarm_audit,
            section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
            is_success=False,
            error_message="",
            has_token_error=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )
        self.assertTrue(self.skillfarm_audit.reset_has_token_error())
