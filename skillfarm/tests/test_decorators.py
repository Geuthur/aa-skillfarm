from unittest.mock import patch

from django.test import TestCase

from app_utils.esi import EsiDailyDowntime

from skillfarm.decorators import log_timing, when_esi_is_available
from skillfarm.hooks import get_extension_logger


class TestDecorators(TestCase):
    @patch("skillfarm.decorators.fetch_esi_status")
    @patch("skillfarm.decorators.IS_TESTING", new=False)
    def test_when_esi_is_available(self, mock_fetch_esi_status):
        # given
        @when_esi_is_available
        def trigger_esi_deco():
            return "Esi is Available"

        # when
        result = trigger_esi_deco()
        # then
        mock_fetch_esi_status.assert_called_once()
        self.assertEqual(result, "Esi is Available")

    @patch("skillfarm.decorators.fetch_esi_status", side_effect=EsiDailyDowntime)
    @patch("skillfarm.decorators.IS_TESTING", new=False)
    def test_esi_is_available_with_downtime(self, mock_fetch_esi_status):
        # given
        @when_esi_is_available
        def trigger_esi_deco():
            return "Daily Downtime detected. Aborting."

        # when
        result = trigger_esi_deco()
        # then
        mock_fetch_esi_status.assert_called_once()
        self.assertIsNone(result)

    @patch("skillfarm.decorators.fetch_esi_status")
    @patch("skillfarm.decorators.IS_TESTING", new=True)
    def test_esi_is_available_with_is_test(self, mock_fetch_esi_status):
        # given
        @when_esi_is_available
        def trigger_esi_deco():
            return "Testing Mode."

        # when
        result = trigger_esi_deco()
        # then
        mock_fetch_esi_status.assert_not_called()
        self.assertEqual(result, "Testing Mode.")

    def test_log_timing(self):
        # given
        logger = get_extension_logger(__name__)

        @log_timing(logger)
        def trigger_log_timing():
            return "Log Timing"

        # when
        result = trigger_log_timing()
        # then
        self.assertEqual(result, "Log Timing")
