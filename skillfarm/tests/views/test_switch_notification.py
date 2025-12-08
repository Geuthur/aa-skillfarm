"""TestView class."""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.utils import (
    create_skillfarm_character_from_user,
)
from skillfarm.views import switch_notification

MODULE_PATH = "skillfarm.views"


class TestSwitchNotificationView(SkillFarmTestCase):
    """Test Switch Notification Ajax Response."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)
        cls.skillfarm_audit_2 = create_skillfarm_character_from_user(cls.superuser)

    def test_switch_notification(self):
        """
        Test should switch notification status for character.
        """
        character_id = self.skillfarm_audit.character.character_id
        form_data = {}

        request = self.factory.post(
            reverse("skillfarm:switch_notification", args=[character_id]),
            data=json.dumps(form_data),
            content_type="application/json",
        )
        request.user = self.user

        response = switch_notification(request, character_id=character_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Notification successfully updated")

    def test_switch_notification_no_permission(self):
        """
        Test should return permission denied when switching notification for character without permission.
        """
        form_data = {}

        request = self.factory.post(
            reverse("skillfarm:switch_notification", args=[1003]),
            data=json.dumps(form_data),
            content_type="application/json",
        )
        request.user = self.user

        response = switch_notification(request, character_id=1003)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")
