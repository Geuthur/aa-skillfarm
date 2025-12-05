"""TestView class."""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.utils import create_skillfarm_character_from_user
from skillfarm.views import delete_character

MODULE_PATH = "skillfarm.views"


class TestDeleteCharacterView(SkillFarmTestCase):
    """
    Test Delete Character Ajax Response.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)
        cls.skillfarm_audit_2 = create_skillfarm_character_from_user(cls.superuser)

    def test_delete_character(self):
        """
        Test should delete own Character successfully.
        """
        character_id = self.skillfarm_audit.character.character_id
        form_data = {
            "character_id": character_id,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("skillfarm:delete_character", args=[character_id]), data=form_data
        )
        request.user = self.user

        response = delete_character(request, character_id=character_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Gneuten successfully deleted")

    def test_delete_character_no_permission(self):
        """
        Test should prevent deleting Character that are not owned by the user.
        """
        form_data = {
            "character_id": 1003,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("skillfarm:delete_character", args=[1003]), data=form_data
        )
        request.user = self.user

        response = delete_character(request, character_id=1003)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")

    def test_delete_character_invalid(self):
        """
        Test should prevent deleting Character with invalid form data.
        """
        request = self.factory.post(
            reverse("skillfarm:delete_character", args=[1003]), data=None
        )
        request.user = self.user
        response = delete_character(request, character_id=1003)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Invalid Form")
