# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.skillfarm import SkillFarmAuditFactory

API_URL = "skillfarm:api"
TASK_PATH = "skillfarm.tasks"


class TestAdminApiEndpoints(SkillFarmTestCase):
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

    def test_get_admin_stats_as_superuser_should_return_aggregated_stats(self):
        # Test Data
        url = reverse(f"{API_URL}:get_admin_stats")
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertGreaterEqual(data["total_characters"], 1)
        self.assertGreaterEqual(data["active_characters"], 1)
        self.assertGreaterEqual(data["in_training_count"], 1)
        self.assertGreaterEqual(data["total_sp"], 5_000_000)
        self.assertGreaterEqual(data["total_pending_extractions"], 2)

    def test_get_admin_stats_as_standard_user_should_return_forbidden(self):
        # Test Data
        url = reverse(f"{API_URL}:get_admin_stats")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @patch(f"{TASK_PATH}.update_all_skillfarm.apply_async")
    def test_trigger_update_all_as_superuser_should_queue_task(self, mock_apply_async):
        # Test Data
        url = reverse(f"{API_URL}:trigger_update_all")
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
            kwargs={"force_refresh": True}, priority=7
        )

    @patch(f"{TASK_PATH}.update_all_skillfarm.apply_async")
    def test_trigger_update_all_as_standard_user_should_return_forbidden(
        self, mock_apply_async
    ):
        # Test Data
        url = reverse(f"{API_URL}:trigger_update_all")
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

    @patch(f"{TASK_PATH}.update_all_prices.apply_async")
    def test_trigger_update_prices_as_superuser_should_queue_task(
        self, mock_apply_async
    ):
        # Test Data
        url = reverse(f"{API_URL}:trigger_update_prices")
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.post(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_apply_async.assert_called_once()
