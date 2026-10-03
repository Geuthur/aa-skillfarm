# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.skillfarm import UserMainFactory

API_URL = "skillfarm:api"


class TestGeneralApiEndpoints(SkillFarmTestCase):
    def test_get_menu_as_standard_user_should_return_menu_without_admin(self):
        # Test Data
        url = reverse(f"{API_URL}:get_menu")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIn("left_links", data)
        self.assertIn("right_links", data)
        left_names = [link["name"] for link in data["left_links"]]
        self.assertIn("Characters", left_names)
        self.assertIn("Calculator", left_names)
        self.assertNotIn("Administration", left_names)
        self.assertNotIn("Overview", left_names)

    def test_get_menu_as_superuser_should_include_administration(self):
        # Test Data
        url = reverse(f"{API_URL}:get_menu")
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        left_names = [link["name"] for link in data["left_links"]]
        self.assertIn("Administration", left_names)

    def test_get_menu_as_admin_permission_user_should_include_administration(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        url = reverse(f"{API_URL}:get_menu")
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        left_names = [link["name"] for link in data["left_links"]]
        self.assertIn("Administration", left_names)

    def test_get_menu_as_corp_access_user_should_include_overview(self):
        # Test Data
        corp_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.corp_access"]
        )
        url = reverse(f"{API_URL}:get_menu")
        self.client.force_login(corp_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        left_names = [link["name"] for link in response.json()["left_links"]]
        self.assertIn("Overview", left_names)
        self.assertNotIn("Administration", left_names)

    def test_get_user_with_permission_should_return_user_data(self):
        # Test Data
        url = reverse(f"{API_URL}:get_user")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["user_id"], self.user.id)
        self.assertEqual(
            data["character_name"], self.user.profile.main_character.character_name
        )
        self.assertFalse(data["is_admin"])

    def test_get_user_without_permission_should_return_forbidden(self):
        # Test Data
        url = reverse(f"{API_URL}:get_user")
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
