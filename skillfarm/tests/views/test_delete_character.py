"""TestView class."""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import SkillFarmAuditFactory
from skillfarm.views import delete_character

MODULE_PATH = "skillfarm.views"


class TestDeleteCharacterView(SkillFarmTestCase):
    """
    Test Delete Character Ajax Response.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = SkillFarmAuditFactory(user=cls.user)
        cls.skillfarm_audit_2 = SkillFarmAuditFactory(user=cls.superuser)

    def test_delete_character(self):
        """
        Test should delete own Character successfully.
        """
        character_id = self.skillfarm_audit.character.character_id
        form_data = {}

        request = self.factory.post(
            reverse("skillfarm:delete_character", args=[character_id]),
            data=json.dumps(form_data),
            content_type="application/json",
        )
        request.user = self.user
        response = delete_character(request, character_id=character_id)

        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["success"])
        self.assertEqual(
            response_data["message"],
            f"{self.skillfarm_audit.character.character_name} successfully deleted",
        )

    def test_delete_character_no_permission(self):
        """
        Test should prevent deleting Character that are not owned by the user.
        """
        form_data = {}

        request = self.factory.post(
            reverse(
                "skillfarm:delete_character",
                args=[self.skillfarm_audit_2.character.character_id],
            ),
            data=json.dumps(form_data),
            content_type="application/json",
        )
        request.user = self.user

        response = delete_character(
            request, character_id=self.skillfarm_audit_2.character.character_id
        )
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Permission Denied")
