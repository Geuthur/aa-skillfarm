# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Third Party
import pook
from aiopenapi3 import RequestError
from evesde_factory.eve_sde import ItemTypeFactory

# Alliance Auth
from esi.exceptions import (
    ESIBucketLimitException,
    ESIErrorLimitException,
    HTTPServerError,
)

# AA Skillfarm
from skillfarm.models.helpers.update_manager import CharacterUpdateSection
from skillfarm.models.skillfarmaudit import CharacterUpdateStatus
from skillfarm.tests import AuthTestCase
from skillfarm.tests.testdata.esi import clear_esi_limits, skillqueue_url
from skillfarm.tests.testdata.skillfarm import SkillFarmAuditFactory

MODULE_PATH = "skillfarm.managers.skillqueue"


class TestSkillQueueManager(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = SkillFarmAuditFactory(user=cls.user)

        cls.eve_type = ItemTypeFactory(id=1)
        cls.eve_type_2 = ItemTypeFactory(id=2)

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
        self.skillfarm_audit.update_skillqueue()
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


class TestSkillQueueManagerEsiErrors(AuthTestCase):
    """ESI errors of the skillqueue section through the real ESI client."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.skillfarm_audit = SkillFarmAuditFactory(user=cls.user)

    def setUp(self):
        super().setUp()
        clear_esi_limits(self.skillfarm_audit)
        self.addCleanup(clear_esi_limits, self.skillfarm_audit)

    def _skillqueue_status(self) -> CharacterUpdateStatus:
        return CharacterUpdateStatus.objects.get(
            owner=self.skillfarm_audit, section=CharacterUpdateSection.SKILLQUEUE
        )

    def test_execute_section_should_record_other_esi_errors(self):
        for status_code in [HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.NOT_FOUND]:
            with self.subTest(status_code=status_code), pook.use():
                # Test Data
                pook.get(
                    skillqueue_url(self.skillfarm_audit),
                    reply=status_code,
                    response_json={"error": status_code.phrase},
                )

                # Test Action
                result = self.skillfarm_audit.execute_section(
                    CharacterUpdateSection.SKILLQUEUE
                )

                # Expected Result
                self.assertFalse(result.is_updated)
                self.assertFalse(result.has_token_error)
                status = self._skillqueue_status()
                self.assertFalse(status.is_success)
                self.assertIn(str(status_code.value), status.error_message)

    def test_execute_section_should_raise_esi_server_errors_to_retry(self):
        for status_code in [
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ]:
            with self.subTest(status_code=status_code), pook.use():
                # Test Data
                pook.get(
                    skillqueue_url(self.skillfarm_audit),
                    reply=status_code,
                    response_json={"error": status_code.phrase},
                )

                # Test Action
                with self.assertRaises(HTTPServerError) as ctx:
                    self.skillfarm_audit.execute_section(
                        CharacterUpdateSection.SKILLQUEUE
                    )

                # Expected Result
                self.assertEqual(ctx.exception.status_code, status_code)
                status = self._skillqueue_status()
                self.assertFalse(status.is_success)
                self.assertIn(str(status_code.value), status.error_message)

    @pook.on
    def test_execute_section_should_raise_the_esi_error_limit_to_retry(self):
        # Test Data
        pook.get(
            skillqueue_url(self.skillfarm_audit),
            reply=420,
            response_json={"error": "Error limited"},
            response_headers={"X-RateLimit-Reset": "30"},
        )

        # Test Action
        with self.assertRaises(ESIErrorLimitException) as ctx:
            self.skillfarm_audit.execute_section(CharacterUpdateSection.SKILLQUEUE)

        # Expected Result
        self.assertEqual(ctx.exception.reset, 30)
        self.assertIn("ESIErrorLimitException", self._skillqueue_status().error_message)

    @pook.on
    def test_execute_section_should_raise_the_esi_bucket_limit_to_retry(self):
        # Test Data: ESI reports the char-detail bucket as used up
        pook.get(
            skillqueue_url(self.skillfarm_audit),
            reply=HTTPStatus.OK,
            response_json=[],
            response_headers={
                "X-Ratelimit-Group": "char-detail",
                "X-Ratelimit-Limit": "600/15m",
                "X-Ratelimit-Remaining": "0",
                "X-Ratelimit-Used": "600",
            },
        )
        self.skillfarm_audit.execute_section(CharacterUpdateSection.SKILLQUEUE)

        # Test Action
        with self.assertRaises(ESIBucketLimitException):
            self.skillfarm_audit.execute_section(
                CharacterUpdateSection.SKILLQUEUE, force_refresh=True
            )

        # Expected Result
        self.assertIn(
            "ESIBucketLimitException", self._skillqueue_status().error_message
        )

    @pook.on
    @patch("esi.app_settings.ESI_SERVER_ERROR_MAX_RETRIES", 1)
    def test_execute_section_should_raise_request_errors_to_retry(self):
        # Test Data: the connection to ESI fails
        pook.get(skillqueue_url(self.skillfarm_audit)).error(
            ConnectionError("Connection reset")
        )

        # Test Action
        with self.assertRaises(RequestError):
            self.skillfarm_audit.execute_section(CharacterUpdateSection.SKILLQUEUE)

        # Expected Result
        self.assertIn("RequestError", self._skillqueue_status().error_message)
