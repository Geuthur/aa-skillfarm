# Standard Library
from unittest.mock import patch

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Skillfarm
from skillfarm import __title__
from skillfarm.decorators import (
    log_timing,
)
from skillfarm.providers import AppLogger
from skillfarm.tests import NoSocketsTestCase

DECORATOR_PATH = "skillfarm.decorators."


class TestDecorators(NoSocketsTestCase):
    def test_log_timing(self):
        """
        Test log_timing decorator to log function execution time.

        :return:
        :rtype:
        """
        # given
        logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)

        @log_timing(logger)
        def trigger_log_timing():
            return "Log Timing"

        # when
        result = trigger_log_timing()
        # then
        self.assertEqual(result, "Log Timing")
