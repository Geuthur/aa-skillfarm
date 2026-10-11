# Standard Library
from unittest.mock import patch

# Django
from django.db import models
from django.db.utils import Error
from django.test import override_settings
from django.utils import timezone

# AA Skillfarm
from skillfarm import tasks
from skillfarm.models.helpers.update_manager import CharacterUpdateSection
from skillfarm.models.prices import EveTypePrice
from skillfarm.models.skillfarmaudit import (
    CharacterSkill,
    SkillFarmAudit,
    SkillFarmSetup,
)
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import EveCharacterFactory
from skillfarm.tests.testdata.skillfarm import (
    CharacterSkillFactory,
    CharacterUpdateStatusFactory,
    EveTypePriceFactory,
    SkillFarmAuditFactory,
    SkillFarmSetupFactory,
    UserMainFactory,
)
from skillfarm.tests.testdata.utils import add_character_to_user

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

        cls.skillfarm_audit = SkillFarmAuditFactory(user=cls.user)

    def test_should_update_all_skillfarm(self, mock_update_character):
        """
        Test should start update_character for each SkillFarmAudit.
        """
        # Test Data
        # setUpClass has initialized cls.skillfarm_audit

        # Test Action
        tasks.update_all_skillfarm()

        # Expected Result
        self.assertTrue(mock_update_character.apply_async.called)

    def test_update_all_skillfarm_should_group_by_user(self, mock_update_character):
        """
        Test should group characters by user and queue alts together.
        """
        # Test Data
        user_1 = UserMainFactory()
        main_1 = SkillFarmAuditFactory(user=user_1)
        alt_1_char = EveCharacterFactory()
        add_character_to_user(
            user=user_1,
            character=alt_1_char,
            is_main=False,
            scopes=SkillFarmAudit.get_esi_scopes(),
        )
        alt_1 = SkillFarmAuditFactory(user=user_1, character=alt_1_char)

        # Test Action
        tasks.update_all_skillfarm()

        # Expected Result
        queued_pks = [
            call.kwargs["args"][0]
            for call in mock_update_character.apply_async.call_args_list
        ]
        self.assertIn(main_1.pk, queued_pks)
        self.assertIn(alt_1.pk, queued_pks)


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
@patch(TASK_PATH + ".logger", spec=True)
class TestUpdateCharacter(SkillFarmTestCase):
    """Test the update_character task."""

    def test_update_character_should_no_updated(self, mock_logger):
        """
        Test should not update character if no updates are needed.
        """
        # Test Data
        user = UserMainFactory()
        audit = SkillFarmAuditFactory(user=user)
        CharacterUpdateStatusFactory(
            character=audit,
            section=CharacterUpdateSection.SKILLS,
            is_success=True,
            error_message="",
            has_token_error=False,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )
        CharacterUpdateStatusFactory(
            character=audit,
            section=CharacterUpdateSection.SKILLQUEUE,
            is_success=True,
            error_message="",
            has_token_error=False,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )

        # Test Action
        tasks.update_character(character_pk=audit.pk)

        # Expected Result
        mock_logger.info.assert_called_once_with(
            "No updates needed for %s",
            audit.character.character_name,
        )

    @patch(TASK_PATH + ".update_char_skills")
    @patch(TASK_PATH + ".update_char_skillqueue")
    def test_update_character_should_update(
        self, mock_skillqueue, mock_skills, mock_logger
    ):
        """
        Test should update character if updates are needed.
        """
        # Test Data
        user = UserMainFactory()
        audit = SkillFarmAuditFactory(user=user)
        CharacterUpdateStatusFactory(
            character=audit,
            section=CharacterUpdateSection.SKILLS,
            is_success=True,
            error_message="",
            has_token_error=False,
            last_run_at=None,
            last_run_finished_at=None,
            last_update_at=None,
            last_update_finished_at=None,
        )

        # Test Action
        tasks.update_character(character_pk=audit.pk)

        # Expected Result
        mock_skills.assert_called_once_with(character_pk=audit.pk, force_refresh=False)

    def test_update_char_skills_should_call_section_update(self, mock_logger):
        # Test Data
        user = UserMainFactory()
        audit = SkillFarmAuditFactory(user=user)

        # Test Action
        with patch.object(tasks, "_update_character_section") as mock_update_section:
            tasks.update_char_skills(character_pk=audit.pk, force_refresh=False)

        # Expected Result
        mock_update_section.assert_called_once()

    def test_update_char_skillqueue_should_call_section_update(self, mock_logger):
        # Test Data
        user = UserMainFactory()
        audit = SkillFarmAuditFactory(user=user)

        # Test Action
        with patch.object(tasks, "_update_character_section") as mock_update_section:
            tasks.update_char_skillqueue(character_pk=audit.pk, force_refresh=False)

        # Expected Result
        mock_update_section.assert_called_once()

    @patch(TASK_PATH + ".update_character.apply_async")
    def test_update_user_characters_should_queue_characters(
        self, mock_apply_async, mock_logger
    ):
        """
        Test that update_user_characters queues all active characters for the given user.
        """
        # Test Data
        user = UserMainFactory()
        main = SkillFarmAuditFactory(user=user)
        alt_char = EveCharacterFactory()
        add_character_to_user(
            user=user,
            character=alt_char,
            is_main=False,
            scopes=SkillFarmAudit.get_esi_scopes(),
        )
        alt = SkillFarmAuditFactory(user=user, character=alt_char, active=True)
        inactive_char = EveCharacterFactory()
        add_character_to_user(
            user=user,
            character=inactive_char,
            is_main=False,
            scopes=SkillFarmAudit.get_esi_scopes(),
        )
        SkillFarmAuditFactory(user=user, character=inactive_char, active=False)

        # Test Action
        tasks.update_user_characters(user_id=user.id, force_refresh=True)

        # Expected Result
        queued_pks = [
            call.kwargs["args"][0] for call in mock_apply_async.call_args_list
        ]
        self.assertIn(main.pk, queued_pks)
        self.assertIn(alt.pk, queued_pks)
        self.assertEqual(len(queued_pks), 2)

    @patch(TASK_PATH + ".update_char_skills")
    @patch(TASK_PATH + ".update_character.apply_async")
    def test_update_character_with_update_alts_should_queue_alts(
        self, mock_apply_async, mock_update_skills, mock_logger
    ):
        """
        Test that update_character queues active alts when update_alts=True.
        """
        # Test Data
        user = UserMainFactory()
        main = SkillFarmAuditFactory(user=user)
        alt_char = EveCharacterFactory()
        add_character_to_user(
            user=user,
            character=alt_char,
            is_main=False,
            scopes=SkillFarmAudit.get_esi_scopes(),
        )
        alt = SkillFarmAuditFactory(user=user, character=alt_char, active=True)

        # Test Action
        tasks.update_character(
            character_pk=main.pk, force_refresh=True, update_alts=True
        )

        # Expected Result
        mock_apply_async.assert_called_once_with(
            args=[alt.pk], kwargs={"force_refresh": True, "update_alts": False}
        )


@patch(TASK_PATH + ".SkillFarmAudit.objects.filter", spec=True)
@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
class TestCheckSkillfarmNotification(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = SkillFarmAuditFactory(user=cls.user)
        cls.skillfarm_audit_2 = SkillFarmAuditFactory(user=cls.no_permission_user)
        cls.skillfarm_audit_3 = SkillFarmAuditFactory(user=cls.superuser)

    def setUp(self):
        super().setUp()
        CharacterSkill.objects.filter(
            character__in=[
                self.skillfarm_audit,
                self.skillfarm_audit_2,
                self.skillfarm_audit_3,
            ]
        ).delete()
        SkillFarmSetup.objects.filter(
            character__in=[
                self.skillfarm_audit,
                self.skillfarm_audit_2,
                self.skillfarm_audit_3,
            ]
        ).delete()
        for audit in [
            self.skillfarm_audit,
            self.skillfarm_audit_2,
            self.skillfarm_audit_3,
        ]:
            audit.refresh_from_db()
            audit.notification = False
            audit.extraction_acknowledged = False
            audit.save()

    def _set_notification_status(
        self, audits: models.QuerySet[SkillFarmAudit], status: bool
    ):
        """Set notification status for SkillFarmAudit."""
        for audit in audits:
            audit.notification = status
            audit.save()

    def test_no_notification_should_return_false(self, mock_audit_filter):
        # Test Data
        audits = [self.skillfarm_audit, self.skillfarm_audit_2]
        self._set_notification_status(audits, False)
        mock_audit_filter.return_value = audits

        # Test Action
        with patch(TASK_PATH + ".send_user_notification") as send_notification:
            tasks.check_skillfarm_notifications()

        # Expected Result
        send_notification.delay.assert_not_called()

    def test_notification_with_no_skillsetup_should_return_false(
        self, mock_audit_filter
    ):
        # Test Data
        audits = [self.skillfarm_audit, self.skillfarm_audit_2, self.skillfarm_audit_3]
        self._set_notification_status(audits, True)
        mock_audit_filter.return_value = audits

        # Test Action
        with patch(TASK_PATH + ".send_user_notification") as send_notification:
            tasks.check_skillfarm_notifications()

        # Expected Result
        send_notification.delay.assert_not_called()

    def test_notification_should_return_true(self, mock_audit_filter):
        # Test Data
        skill = CharacterSkillFactory(
            character=self.skillfarm_audit,
            trained_skill_level=5,
        )
        SkillFarmSetupFactory(
            character=self.skillfarm_audit,
            skillset=[skill.eve_type.name],
        )

        audits = [self.skillfarm_audit]
        self._set_notification_status(audits, True)

        # Ensure we operate on fresh model instances
        self.skillfarm_audit.refresh_from_db()

        mock_audit_filter.return_value = audits

        # Test Action
        with patch(TASK_PATH + ".send_user_notification") as send_notification:
            tasks.check_skillfarm_notifications()

        # Expected Result
        send_notification.delay.assert_called_once()

    def test_notification_should_not_notify_when_acknowledged(self, mock_audit_filter):
        """
        Test should not send notification if extraction has already been acknowledged.
        """
        # Test Data
        skill = CharacterSkillFactory(
            character=self.skillfarm_audit_2,
            trained_skill_level=5,
        )
        SkillFarmSetupFactory(
            character=self.skillfarm_audit_2,
            skillset=[skill.eve_type.name],
        )

        audits = [self.skillfarm_audit_2]
        self._set_notification_status(audits, True)
        self.skillfarm_audit_2.extraction_acknowledged = True
        self.skillfarm_audit_2.save()
        self.skillfarm_audit_2.refresh_from_db()

        mock_audit_filter.return_value = audits

        # Test Action
        with patch(TASK_PATH + ".send_user_notification") as send_notification:
            tasks.check_skillfarm_notifications()

        # Expected Result
        send_notification.delay.assert_not_called()

    @patch(TASK_PATH + ".logger", spec=True)
    def test_notification_no_main_should_return_false(
        self, mock_logger, mock_audit_filter
    ):
        """
        Test should not send notification if no main character is found.
        """
        # Test Data
        user_no_main = UserMainFactory()
        audit = SkillFarmAuditFactory(user=user_no_main)
        audit.notification = True
        audit.save()

        user_no_main.profile.main_character = None
        user_no_main.profile.save()
        user_no_main.refresh_from_db()
        audit.refresh_from_db()

        mock_audit_filter.return_value = [audit]

        # Test Action
        with patch(TASK_PATH + ".send_user_notification") as send_notification:
            tasks.check_skillfarm_notifications()

        # Expected Result
        send_notification.delay.assert_not_called()
        mock_logger.warning.assert_called_once_with(
            "Main Character not found for %s, skipping notification",
            audit.character.character_name,
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

        cls.price = EveTypePriceFactory(
            name="TestPrice",
            eve_type_id=44992,
            buy=100,
            sell=200,
            updated_at=timezone.now(),
        )
        cls.price2 = EveTypePriceFactory(
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
