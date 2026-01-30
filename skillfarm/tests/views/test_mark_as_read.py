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
from skillfarm.views import mark_as_read

MODULE_PATH = "skillfarm.views"


class TestMarkAsReadView(SkillFarmTestCase):
    """Test Mark As Read Ajax Response."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)
        cls.skillfarm_audit_2 = create_skillfarm_character_from_user(cls.superuser)

    def test_mark_as_read(self):
        """
        Test should mark as read notification status for character.
        """
        character_id = self.skillfarm_audit.character.character_id
        form_data = {}

        request = self.factory.post(
            reverse("skillfarm:mark_as_read", args=[character_id]),
            data=json.dumps(form_data),
            content_type="application/json",
        )
        request.user = self.user

        response = mark_as_read(request, character_id=character_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["message"],
            f"{self.skillfarm_audit.character.character_name} successfully toggled Mark as Read",
        )

    def test_mark_as_read_no_permission(self):
        """
        Test should return permission denied when marking as read for character without permission.
        """
        form_data = {}

        request = self.factory.post(
            reverse("skillfarm:mark_as_read", args=[1003]),
            data=json.dumps(form_data),
            content_type="application/json",
        )
        request.user = self.user

        response = mark_as_read(request, character_id=1003)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")
