# Django
from django.utils import timezone

# Alliance Auth
from esi.errors import TokenError
from esi.exceptions import HTTPClientError, HTTPNotModified, HTTPServerError

# AA Skillfarm
from skillfarm.models.skillfarmaudit import (
    CharacterUpdateStatus,
    SkillFarmAudit,
    UpdateSectionResult,
)
from skillfarm.tests import SkillFarmTestCase
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
        cls.no_token_audit = create_skillfarm_character_from_user(
            cls.no_permission_user
        )

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

    def test_get_token_should_return_token(self):
        """
        Test should return valid token.
        """
        token = self.skillfarm_audit.get_token()
        self.assertIsNotNone(token)

    def test_get_token_should_raise_token_error(self):
        """
        Test should raise TokenError when no valid token exists.
        """
        with self.assertRaises(TokenError):
            self.no_token_audit.get_token()

    def test_perform_update_status(self):
        """
        Test the perform_update_status method for token error scenario.
        """
        # Test Data
        create_update_status(
            character_audit=self.skillfarm_audit,
            section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
            error_message="",
        )

        def mock_update_method():
            return UpdateSectionResult(
                is_changed=True,
                is_updated=True,
                has_token_error=False,
            )

        # Test Action
        result = self.skillfarm_audit.perform_update_status(
            section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
            method=mock_update_method,
        )

        # Expected Results
        self.assertIsInstance(result, UpdateSectionResult)
        self.assertTrue(result.is_changed)
        self.assertTrue(result.is_updated)

    def test_perform_update_Status_token_error(self):
        """
        Test the perform_update_status method for token error scenario.
        """
        # Test Data
        status_obj = create_update_status(
            character_audit=self.skillfarm_audit,
            section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
            error_message="",
        )

        def mock_update_method():
            raise ValueError("Token error occurred.")

        # Test Action: perform_update_status should persist an error and re-raise
        with self.assertRaises(ValueError):
            self.skillfarm_audit.perform_update_status(
                section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
                method=mock_update_method,
            )

        # Expected Results: status object updated due to the exception
        status_obj = CharacterUpdateStatus.objects.get(
            character=self.skillfarm_audit,
            section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
        )
        self.assertFalse(status_obj.is_success)
        self.assertFalse(status_obj.has_token_error)
        self.assertIn("ValueError: Token error occurred.", status_obj.error_message)

    def test_perform_update_Status_httpserver_error(self):
        """
        Test the perform_update_status method for HTTPServerError scenario.
        """
        # Test Data
        status_obj = create_update_status(
            character_audit=self.skillfarm_audit,
            section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
            error_message="",
        )

        def mock_update_method():
            raise HTTPServerError(status_code=500, headers={}, data=None)

        # Test Action: perform_update_status should persist an error and re-raise
        with self.assertRaises(HTTPServerError):
            self.skillfarm_audit.perform_update_status(
                section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
                method=mock_update_method,
            )

        # Expected Results: status object updated due to the exception
        status_obj = CharacterUpdateStatus.objects.get(
            character=self.skillfarm_audit,
            section=SkillFarmAudit.UpdateSection.SKILLQUEUE,
        )
        self.assertFalse(status_obj.is_success)
        self.assertFalse(status_obj.has_token_error)
