# Standard Library
from unittest.mock import patch

# Django
from django.db import models
from django.db.utils import Error
from django.test import override_settings
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import UserProfile

# AA Skillfarm
from skillfarm import tasks
from skillfarm.models.prices import EveTypePrice
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tests import NoSocketsTestCase, SkillFarmTestCase
from skillfarm.tests.testdata.utils import (
    create_character_skill,
    create_eve_type_price,
    create_skillfarm_character_from_user,
    create_skillsetup_character,
    create_update_status,
)

TASK_PATH = "skillfarm.tasks"


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
@patch(TASK_PATH + ".update_character", spec=True)
class TestUpdateAllSkillfarm(SkillFarmTestCase):
    """Test the update_all_skillfarm task."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)

    def test_should_update_all_skillfarm(self, mock_update_all_skillfarm):
        """
            Test should start update_character for each SkillFarmAudit.
        :return:
        :rtype:
        """
        # when
        tasks.update_all_skillfarm()
        # then
        self.assertTrue(mock_update_all_skillfarm.apply_async.called)


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
@patch(TASK_PATH + ".chain", spec=True)
@patch(TASK_PATH + ".logger", spec=True)
class TestUpdateCharacter(SkillFarmTestCase):
    """Test the update_character task."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)

    def test_update_character_should_no_updated(self, mock_logger, __):
        """
        Test should not update character if no updates are needed.
        """
        # when
        tasks.update_character(self.skillfarm_audit.pk)
        # then
        mock_logger.info.assert_called_once_with(
            "No updates needed for %s",
            self.skillfarm_audit.character.character_name,
        )

    def test_update_character_should_update(self, mock_logger, mock_chain):
        """
        Test should update character if updates are needed.
        """
        # given
        create_update_status(
            self.skillfarm_audit,
            section=SkillFarmAudit.UpdateSection.SKILLS,
            is_success=True,
            error_message="",
            has_token_error=False,
            last_run_at=None,
            last_run_finished_at=None,
            last_update_at=None,
            last_update_finished_at=None,
        )

        # when
        tasks.update_character(self.skillfarm_audit.pk)
        # then
        mock_chain.assert_called_once()


@patch(TASK_PATH + ".SkillFarmAudit.objects.filter", spec=True)
@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
class TestCheckSkillfarmNotification(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)
        cls.skillfarm_audit_2 = create_skillfarm_character_from_user(
            cls.no_permission_user
        )
        cls.skillfarm_audit_3 = create_skillfarm_character_from_user(cls.superuser)

    def _set_notification_status(
        self, audits: models.QuerySet[SkillFarmAudit], status: bool
    ):
        """Set notification status for SkillFarmAudit."""
        for audit in audits:
            audit.notification = status
            audit.save()

    def test_no_notification_should_return_false(self, mock_audit_filter):
        """
        Test should not send notification if notification is disabled.
        """
        # given
        audits = [self.skillfarm_audit, self.skillfarm_audit_2]
        self._set_notification_status(audits, False)
        mock_audit_filter.return_value = audits
        # when
        tasks.check_skillfarm_notifications()
        # then
        for audit in audits:
            self.assertFalse(audit.notification_sent)
            self.assertIsNone(audit.last_notification)

    def test_notifiaction_with_no_skillsetup_should_return_false(
        self, mock_audit_filter
    ):
        """
        Test should not send notification if no SkillFarmSetup is found.
        """
        audits = [self.skillfarm_audit, self.skillfarm_audit_2, self.skillfarm_audit_3]
        self._set_notification_status(audits, True)
        mock_audit_filter.return_value = audits
        # when
        tasks.check_skillfarm_notifications()
        # then
        for audit in audits:
            self.assertFalse(audit.notification_sent)
            self.assertIsNone(audit.last_notification)

    def test_notification_should_return_true(self, mock_audit_filter):
        """
        Test should send notification if notification is enabled and SkillFarmSetup exists.
        """
        # given
        create_skillsetup_character(
            character_id=self.skillfarm_audit.character.character_id,
            skillset=["skill1"],
        )
        create_character_skill(
            character_id=self.skillfarm_audit.character.character_id, evetype_id=1
        )
        # Ensure we operate on fresh model instances
        self.skillfarm_audit.refresh_from_db()

        audits = [self.skillfarm_audit]
        self._set_notification_status(audits, True)

        mock_audit_filter.return_value = audits
        # when
        tasks.check_skillfarm_notifications()
        # then
        for audit in audits:
            self.assertTrue(audit.notification_sent)
            self.assertIsNotNone(audit.last_notification)

    @patch(TASK_PATH + ".logger", spec=True)
    def test_notifiaction_no_main_should_return_false(
        self, mock_logger, mock_audit_filter
    ):
        """
        Test should not send notification if no main character is found.
        """
        audits = [self.skillfarm_audit]
        self._set_notification_status(audits, True)

        # Delete the main character and clear the relation
        self.user.profile.main_character = None
        self.user.profile.save()
        self.user.profile.refresh_from_db()

        # Ensure we operate on fresh model instances (no cached relations)
        audits = [SkillFarmAudit.objects.get(pk=audit.pk) for audit in audits]

        mock_audit_filter.return_value = audits
        # when
        tasks.check_skillfarm_notifications()
        # then
        for audit in audits:
            self.assertFalse(audit.notification_sent)
            self.assertIsNone(audit.last_notification)
            mock_logger.warning.assert_called_once_with(
                "Main Character not found for %s, skipping notification",
                self.skillfarm_audit.character.character_name,
            )


@patch(TASK_PATH + ".requests.get", spec=True)
@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
class TestSkillfarmPrices(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.price = create_eve_type_price(
            name="TestPrice",
            eve_type_id=44992,
            buy=100,
            sell=200,
            updated_at=timezone.now(),
        )
        cls.price2 = create_eve_type_price(
            name="TestPrice2",
            eve_type_id=40519,
            buy=300,
            sell=400,
            updated_at=timezone.now(),
        )

        cls.json = {
            "44992": {
                "buy": {"percentile": 100},
                "sell": {"percentile": 200},
            }
        }

    @patch(TASK_PATH + ".EveTypePrice.objects.all", spec=True)
    @patch(TASK_PATH + ".logger", spec=True)
    def test_update_prices_should_update_nothing(
        self, mock_logger, mock_prices, mock_requests
    ):
        """
        Test should not update prices if no prices exist.
        """
        mock_prices.return_value = []
        mock_response = mock_requests.return_value
        mock_response.json.return_value = self.json

        # when
        tasks.update_all_prices()
        # then
        mock_logger.info.assert_called_once_with("No Prices to update")

    def test_should_update_prices(self, mock_requests):
        """
        Test should update existing prices.
        """
        mock_response = mock_requests.return_value
        mock_response.json.return_value = self.json
        old_updated_at = self.price.updated_at
        # when
        tasks.update_all_prices()
        self.price.refresh_from_db()
        # then
        self.assertEqual(self.price.buy, 100)
        self.assertEqual(self.price.sell, 200)
        self.assertGreater(self.price.updated_at, old_updated_at)

    def test_update_prices_should_only_update_existing(self, mock_requests):
        """
        Test should only update existing prices.
        """
        mock_response = mock_requests.return_value
        changed_json = self.json.copy()
        changed_json.update(
            {
                4: {
                    "buy": {"percentile": 300},
                    "sell": {"percentile": 400},
                }
            }
        )
        mock_response.json.return_value = changed_json
        # when
        tasks.update_all_prices()
        self.price.refresh_from_db()
        # then
        self.assertIsNone(EveTypePrice.objects.filter(eve_type__id=4).first())

    @patch(TASK_PATH + ".EveTypePrice.objects.bulk_update", spec=True)
    @patch(TASK_PATH + ".logger", spec=True)
    def test_update_prices_should_raise_exception(
        self, mock_logger, mock_bulk_update, mock_requests
    ):
        """
        Test should log error if bulk_update raises an exception.
        """
        mock_response = mock_requests.return_value
        mock_response.json.return_value = self.json
        error_instance = Error("Error")
        mock_bulk_update.side_effect = error_instance
        # when
        tasks.update_all_prices()
        # then
        mock_logger.error.assert_called_once_with(
            "Error updating prices: %s", error_instance
        )
