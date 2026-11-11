# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Third Party
import pook
from aiopenapi3 import RequestError
from celery import Task, states
from celery.exceptions import Retry
from evesde_factory.allianceauth import EveCharacterFactory
from evesde_factory.utils import add_character_to_user

# Django
from django.core.cache import cache
from django.db import models
from django.db.utils import Error
from django.test import override_settings
from django.utils import timezone

# Alliance Auth
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPServerError,
)

# AA Skillfarm
from skillfarm import tasks
from skillfarm.errors import DownTimeError
from skillfarm.models.helpers.update_manager import CharacterUpdateSection
from skillfarm.models.prices import EveTypePrice
from skillfarm.models.skillfarmaudit import (
    CharacterSkill,
    CharacterUpdateStatus,
    SkillFarmAudit,
    SkillFarmSetup,
)
from skillfarm.providers import DOWNTIME_TIMER
from skillfarm.tests import AuthTestCase
from skillfarm.tests.testdata.esi import clear_esi_limits, skillqueue_url, skills_url
from skillfarm.tests.testdata.skillfarm import (
    CharacterSkillFactory,
    CharacterUpdateStatusFactory,
    EveTypePriceFactory,
    SkillFarmAuditFactory,
    SkillFarmSetupFactory,
    UserMainFactory,
)

TASK_PATH = "skillfarm.tasks"


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
@patch(TASK_PATH + ".update_character", spec=True)
class TestUpdateAllSkillfarm(AuthTestCase):
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
class TestUpdateCharacter(AuthTestCase):
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
    @patch(TASK_PATH + ".update_char_skillqueue")
    @patch(TASK_PATH + ".update_character.apply_async")
    def test_update_character_with_update_alts_should_queue_alts(
        self, mock_apply_async, mock_update_skillqueue, mock_update_skills, mock_logger
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


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch.object(tasks.update_character, "retry", side_effect=Retry)
class TestUpdateCharacterEsiErrors(AuthTestCase):
    """ESI errors of a section reach `retry_task_on_esi_error` through the UpdateManager."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = SkillFarmAuditFactory(user=cls.user)

    def setUp(self):
        super().setUp()
        clear_esi_limits(self.audit)
        self.addCleanup(clear_esi_limits, self.audit)

    def _assert_retried(self, mock_retry, exc_type, countdown_min: float):
        mock_retry.assert_called_once()
        kwargs = mock_retry.call_args.kwargs
        self.assertIsInstance(kwargs["exc"], exc_type)
        self.assertGreaterEqual(kwargs["countdown"], countdown_min)
        status = CharacterUpdateStatus.objects.get(
            owner=self.audit, section=CharacterUpdateSection.SKILLS
        )
        self.assertFalse(status.is_success)
        self.assertTrue(status.error_message.startswith(exc_type.__name__))

    def test_should_retry_on_esi_server_errors(self, mock_retry):
        for status_code in [
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ]:
            with self.subTest(status_code=status_code), pook.use():
                # Test Data
                mock_retry.reset_mock()
                pook.get(
                    skills_url(self.audit),
                    reply=status_code,
                    response_json={"error": status_code.phrase},
                )

                # Test Action
                with self.assertRaises(Retry):
                    tasks.update_character(self.audit.pk, force_refresh=True)

                # Expected Result
                self._assert_retried(mock_retry, HTTPServerError, DOWNTIME_TIMER)

    @pook.on
    def test_should_retry_on_the_esi_error_limit(self, mock_retry):
        # Test Data
        pook.get(
            skills_url(self.audit),
            reply=420,
            response_json={"error": "Error limited"},
            response_headers={"X-RateLimit-Reset": "30"},
        )

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_character(self.audit.pk, force_refresh=True)

        # Expected Result
        self._assert_retried(mock_retry, ESIErrorLimitException, 30)

    @pook.on
    def test_should_retry_on_the_esi_bucket_limit(self, mock_retry):
        # Test Data: the char-detail bucket of the character is used up
        cache.set(
            f"esi:bucket:char-detail:{self.audit.character.character_id}",
            0,
            timeout=900,
        )

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_character(self.audit.pk, force_refresh=True)

        # Expected Result
        self._assert_retried(mock_retry, ESIBucketLimitException, 1)

    @pook.on
    @patch("esi.app_settings.ESI_SERVER_ERROR_MAX_RETRIES", 1)
    def test_should_retry_on_request_errors(self, mock_retry):
        # Test Data
        pook.get(skills_url(self.audit)).error(ConnectionError("Connection reset"))

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_character(self.audit.pk, force_refresh=True)

        # Expected Result
        self._assert_retried(mock_retry, RequestError, DOWNTIME_TIMER)

    @patch(TASK_PATH + ".SkillFarmAudit.update_skills", autospec=True)
    def test_should_retry_on_downtime_errors_of_a_section(
        self, mock_update_skills, mock_retry
    ):
        # Test Data
        mock_update_skills.side_effect = DownTimeError("ESI is in daily downtime")

        # Test Action
        with self.assertRaises(Retry):
            tasks.update_character(self.audit.pk, force_refresh=True)

        # Expected Result
        self._assert_retried(mock_retry, DownTimeError, DOWNTIME_TIMER)

    @override_settings(DISABLE_DAILY_DOWNTIME_CHECK=False)
    @patch(TASK_PATH + ".SkillFarmAudit.execute_section")
    def test_should_retry_during_the_daily_downtime(
        self, mock_execute_section, mock_retry
    ):
        # Test Data
        with patch("skillfarm.providers.timezone.now") as mock_now:
            mock_now.return_value = timezone.datetime.strptime("11:05", "%H:%M")

            # Test Action
            with self.assertRaises(Retry):
                tasks.update_character(self.audit.pk, force_refresh=True)

        # Expected Result
        mock_execute_section.assert_not_called()
        self.assertIsInstance(mock_retry.call_args.kwargs["exc"], DownTimeError)

    def test_should_record_other_esi_errors_without_retry(self, mock_retry):
        for status_code in [HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.NOT_FOUND]:
            with self.subTest(status_code=status_code), pook.use():
                # Test Data
                for url in (skills_url(self.audit), skillqueue_url(self.audit)):
                    pook.get(
                        url,
                        reply=status_code,
                        response_json={"error": status_code.phrase},
                    )

                # Test Action
                result = tasks.update_character(self.audit.pk, force_refresh=True)

                # Expected Result
                self.assertTrue(result)
                mock_retry.assert_not_called()
                for section in CharacterUpdateSection:
                    status = CharacterUpdateStatus.objects.get(
                        owner=self.audit, section=section
                    )
                    self.assertFalse(status.is_success)
                    self.assertIn(str(status_code.value), status.error_message)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestUpdateCharSectionEsiErrors(AuthTestCase):
    """The section tasks retry on their own when they run alone."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = SkillFarmAuditFactory(user=cls.user)

    def setUp(self):
        super().setUp()
        clear_esi_limits(self.audit)
        self.addCleanup(clear_esi_limits, self.audit)

    @pook.on
    def test_section_tasks_should_retry_on_esi_server_errors(self):
        for task, url in (
            (tasks.update_char_skills, skills_url(self.audit)),
            (tasks.update_char_skillqueue, skillqueue_url(self.audit)),
        ):
            with (
                self.subTest(task=task.name),
                patch.object(task, "retry", side_effect=Retry) as mock_retry,
            ):
                # Test Data
                pook.get(
                    url,
                    reply=HTTPStatus.BAD_GATEWAY,
                    response_json={"error": "Bad Gateway"},
                )

                # Test Action
                with self.assertRaises(Retry):
                    task(character_pk=self.audit.pk, force_refresh=True)

                # Expected Result
                mock_retry.assert_called_once()
                self.assertIsInstance(
                    mock_retry.call_args.kwargs["exc"], HTTPServerError
                )


@patch(TASK_PATH + ".SkillFarmAudit.objects.filter", spec=True)
@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
)
class TestCheckSkillfarmNotification(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = SkillFarmAuditFactory(user=cls.user)
        cls.no_permission_user = UserMainFactory(permissions__=[])
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
class TestSkillfarmPrices(AuthTestCase):
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


class TestUpdateCharacterQueueOnce(AuthTestCase):
    """`update_character` runs only once per `character_pk` at a time."""

    def setUp(self):
        super().setUp()
        self._clear_locks()
        self.addCleanup(self._clear_locks)

    @staticmethod
    def _clear_locks():
        for character_pk in (1, 2):
            key = tasks.update_character.get_key(args=[character_pk], kwargs={})
            tasks.update_character.once_backend.clear_lock(key)

    @patch.object(Task, "apply_async")
    def test_should_skip_second_apply_async_for_same_character(self, mock_apply_async):
        # when
        tasks.update_character.apply_async(args=[1])
        result = tasks.update_character.apply_async(args=[1])
        # then
        mock_apply_async.assert_called_once()
        self.assertEqual(result.state, states.REJECTED)

    @patch.object(Task, "apply_async")
    def test_should_queue_apply_async_for_other_character(self, mock_apply_async):
        # when
        tasks.update_character.apply_async(args=[1])
        tasks.update_character.apply_async(args=[2])
        # then
        self.assertEqual(mock_apply_async.call_count, 2)
