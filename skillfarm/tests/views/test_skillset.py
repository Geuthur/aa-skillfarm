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
from skillfarm.views import edit_skillsetup

MODULE_PATH = "skillfarm.views"


class TestSkillSetView(SkillFarmTestCase):
    """Test Skillset Ajax Response."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)

    def test_skillset(self):
        """
        Test should update skillset successfully.
        """
        character_id = self.skillfarm_audit.character.character_id
        # SlimSelect Data Types: https://slimselectjs.com/data#types
        form_data = {
            "character_id": character_id,
            "confirm": "yes",
            "selected_skills": json.dumps(
                [
                    {
                        "id": "6v8twmoh",
                        "value": "Abyssal Ore Processing",
                        "text": "Abyssal Ore Processing",
                        "html": "",
                        "defaultSelected": False,
                        "selected": False,
                        "display": True,
                        "disabled": False,
                        "mandatory": False,
                        "placeholder": False,
                        "class": "",
                        "style": "",
                        "data": {},
                    },
                    {
                        "id": "4xf648s5",
                        "value": "Acceleration Control",
                        "text": "Acceleration Control",
                        "html": "",
                        "defaultSelected": False,
                        "selected": False,
                        "display": True,
                        "disabled": False,
                        "mandatory": False,
                        "placeholder": False,
                        "class": "",
                        "style": "",
                        "data": {},
                    },
                ]
            ),
        }
        request = self.factory.post(
            reverse("skillfarm:edit_skillsetup", args=[character_id]),
            data=json.dumps(form_data),
            content_type="application/json",
        )
        request.user = self.user

        response = edit_skillsetup(request, character_id=character_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["message"], "Gneuten Skillset successfully updated"
        )

    def test_skillset_no_permission(self):
        """
        Test should prevent skillset update for Character that are not owned by the User.
        """
        form_data = {
            "character_id": 1003,
            "confirm": "yes",
            "selected_skills": json.dumps(
                [
                    {
                        "id": "6v8twmoh",
                        "value": "Abyssal Ore Processing",
                        "text": "Abyssal Ore Processing",
                        "html": "",
                        "defaultSelected": False,
                        "selected": False,
                        "display": True,
                        "disabled": False,
                        "mandatory": False,
                        "placeholder": False,
                        "class": "",
                        "style": "",
                        "data": {},
                    },
                    {
                        "id": "4xf648s5",
                        "value": "Acceleration Control",
                        "text": "Acceleration Control",
                        "html": "",
                        "defaultSelected": False,
                        "selected": False,
                        "display": True,
                        "disabled": False,
                        "mandatory": False,
                        "placeholder": False,
                        "class": "",
                        "style": "",
                        "data": {},
                    },
                ]
            ),
        }

        request = self.factory.post(
            reverse("skillfarm:edit_skillsetup", args=[1003]),
            data=json.dumps(form_data),
            content_type="application/json",
        )
        request.user = self.user

        response = edit_skillsetup(request, character_id=1003)
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")
