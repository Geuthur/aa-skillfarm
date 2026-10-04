# Standard Library
from unittest.mock import patch

# AA Skillfarm
from skillfarm.helpers.discord import send_user_notification
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.skillfarm import (
    UserMainFactory,
    UserSettingsFactory,
)


class TestUserNotificationSettings(SkillFarmTestCase):
    def test_send_user_notification_should_skip_delivery_when_disabled(self):
        # Test Data
        user = UserMainFactory()
        UserSettingsFactory(user=user, disable_notifications=True)

        # Test Action
        with patch("skillfarm.helpers.discord.notify.info") as notify_info:
            send_user_notification.run(
                user_id=user.id,
                title="Test notification",
                message="This must not be sent",
            )

        # Expected Result
        notify_info.assert_not_called()

    def test_send_user_notification_should_deliver_when_enabled(self):
        # Test Data
        user = UserMainFactory()
        UserSettingsFactory(user=user, disable_notifications=False)

        # Test Action
        with patch("skillfarm.helpers.discord.notify.info") as notify_info:
            send_user_notification.run(
                user_id=user.id,
                title="Test notification",
                message="This should be sent",
            )

        # Expected Result
        notify_info.assert_called_once_with(
            user=user,
            title="Test notification",
            message="This should be sent",
        )
