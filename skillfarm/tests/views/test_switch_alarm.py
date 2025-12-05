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
from skillfarm.views import switch_alarm

MODULE_PATH = "skillfarm.views"


class TestSwitchalarmView(SkillFarmTestCase):
    """Test Switchalarm Ajax Response."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)
        cls.skillfarm_audit_2 = create_skillfarm_character_from_user(cls.superuser)

    def test_switch_alarm(self):
        """
        Test should switch alarm status for character.
        """
        character_id = self.skillfarm_audit.character.character_id
        form_data = {
            "character_id": character_id,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("skillfarm:switch_alarm", args=[character_id]), data=form_data
        )
        request.user = self.user

        response = switch_alarm(request, character_id=character_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Alarm successfully updated")

    def test_switch_alarm_no_permission(self):
        """
        Test should return permission denied when switching alarm for character without permission.
        """
        form_data = {
            "character_id": 1003,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("skillfarm:switch_alarm", args=[1003]), data=form_data
        )
        request.user = self.user

        response = switch_alarm(request, character_id=1003)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")

    def test_switch_alarm_invalid(self):
        """
        Test should return bad request when form is invalid.
        """
        request = self.factory.post(
            reverse("skillfarm:switch_alarm", args=[1001]), data=None
        )
        request.user = self.user

        response = switch_alarm(request, character_id=1001)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Invalid Form")
