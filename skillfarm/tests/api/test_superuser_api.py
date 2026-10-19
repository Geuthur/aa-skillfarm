# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.skillfarm import SkillFarmAuditFactory

API_URL = "skillfarm:api"
TASK_PATH = "skillfarm.tasks"


class TestSuperuserApiEndpoints(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = SkillFarmAuditFactory(
            user=cls.user,
            is_training=True,
            total_sp=5_000_000,
            extractions_ready_count=2,
            extraction_acknowledged=False,
        )

    def test_get_menu_should_include_superuser_link_for_superuser(self):
        # Test Data
        url = reverse(f"{API_URL}:get_menu")
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        right_links = data.get("right_links", [])
        superuser_link = next(
            (link for link in right_links if link["name"] == "Superuser"), None
        )
        self.assertIsNotNone(superuser_link)
        self.assertEqual(superuser_link["link"], "/superuser/")
        self.assertFalse(superuser_link["is_external"])

    def test_get_menu_should_not_include_superuser_link_for_regular_user(self):
        # Test Data
        url = reverse(f"{API_URL}:get_menu")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        right_links = data.get("right_links", [])
        superuser_link = next(
            (link for link in right_links if link["name"] == "Superuser"), None
        )
        self.assertIsNone(superuser_link)

    def test_list_all_audits_as_superuser_should_return_all_audits(self):
        # Test Data
        url = reverse(f"{API_URL}:list_all_audits")
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        found = any(
            item["character_id"] == self.audit.character.character_id for item in data
        )
        self.assertTrue(found)

    def test_list_all_audits_as_regular_user_should_return_forbidden(self):
        # Test Data
        url = reverse(f"{API_URL}:list_all_audits")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @patch(f"{TASK_PATH}.update_character.apply_async")
    def test_trigger_audit_update_as_superuser_should_queue_task(
        self, mock_apply_async
    ):
        # Test Data
        url = reverse(
            f"{API_URL}:trigger_audit_update",
            kwargs={"character_id": self.audit.character.character_id},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(
            url,
            data={"force_refresh": True},
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_apply_async.assert_called_once_with(
            args=[self.audit.pk],
            kwargs={"force_refresh": True},
            priority=7,
        )

    @patch(f"{TASK_PATH}.update_character.apply_async")
    def test_trigger_audit_update_as_regular_user_should_return_forbidden(
        self, mock_apply_async
    ):
        # Test Data
        url = reverse(
            f"{API_URL}:trigger_audit_update",
            kwargs={"character_id": self.audit.character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(
            url,
            data={"force_refresh": False},
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        mock_apply_async.assert_not_called()

    def test_inspect_audit_as_superuser_should_return_character_detail(self):
        # Test Data
        url = reverse(
            f"{API_URL}:inspect_audit",
            kwargs={"character_id": self.audit.character.character_id},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIn("character", data)
        self.assertEqual(
            data["character"]["character_id"], self.audit.character.character_id
        )

    def test_inspect_audit_as_regular_user_should_return_forbidden(self):
        # Test Data
        url = reverse(
            f"{API_URL}:inspect_audit",
            kwargs={"character_id": self.audit.character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_audit_as_regular_user_should_return_forbidden(self):
        # Test Data
        url = reverse(
            f"{API_URL}:delete_audit",
            kwargs={"character_id": self.audit.character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_audit_as_superuser_should_delete_audit(self):
        # Test Data
        audit_to_delete = SkillFarmAuditFactory()
        char_id = audit_to_delete.character.character_id
        url = reverse(
            f"{API_URL}:delete_audit",
            kwargs={"character_id": char_id},
        )
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(
            SkillFarmAudit.objects.filter(character__character_id=char_id).exists()
        )
