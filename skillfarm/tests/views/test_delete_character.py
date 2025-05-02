"""TestView class."""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# AA Skillfarm
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import (
    create_skillfarm_character,
    create_user_from_evecharacter_with_access,
)
from skillfarm.views import delete_character

MODULE_PATH = "skillfarm.views"


class TestDeleteCharacterView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.audit = create_skillfarm_character(1001)
        cls.user = cls.audit.character.character_ownership.user
        cls.no_audit_user, _ = create_user_from_evecharacter_with_access(1002)

    def test_delete_character(self):
        character_id = self.audit.character.character_id
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

    def test_delete_character_no_audit(self):
        form_data = {
            "character_id": 1001,
            "confirm": "yes",
        }

        request = self.factory.post(
            reverse("skillfarm:delete_character", args=[1001]), data=form_data
        )
        request.user = self.no_audit_user

        response = delete_character(request, character_id=1001)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")

    def test_delete_character_invalid(self):
        request = self.factory.post(
            reverse("skillfarm:delete_character", args=[1001]), data=None
        )
        request.user = self.no_audit_user

        response = delete_character(request, character_id=1001)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Invalid Form")
