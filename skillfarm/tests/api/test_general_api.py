# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.models.general import UserSettings
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.skillfarm import UserMainFactory

API_URL = "skillfarm:api"


class TestGeneralApiEndpoints(SkillFarmTestCase):
    def setUp(self):
        super().setUp()
        UserSettings.objects.filter(user=self.user).delete()

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
        right_names = [link["name"] for link in data["right_links"]]
        self.assertIn("My Characters", left_names)
        self.assertIn("Overview", left_names)
        self.assertIn("Calculator", left_names)
        self.assertIn("Settings", left_names)
        self.assertNotIn("Superuser", right_names)
        self.assertNotIn("Overview", right_names)

    def test_get_menu_with_character_error_should_set_has_errors_on_settings(self):
        # Test Data
        # AA Skillfarm
        from skillfarm.models.helpers.update_manager import CharacterUpdateSection
        from skillfarm.tests.testdata.skillfarm import (
            CharacterUpdateStatusFactory,
            SkillFarmAuditFactory,
        )

        audit = SkillFarmAuditFactory(
            user=self.user,
            character=self.user_character,
            active=True,
        )
        CharacterUpdateStatusFactory(
            owner=audit,
            section=CharacterUpdateSection.SKILLS,
            is_success=False,
            has_token_error=False,
            error_message="ESI error",
        )
        url = reverse(f"{API_URL}:get_menu")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        settings_link = next(
            link for link in data["left_links"] if link["name"] == "Settings"
        )
        self.assertTrue(settings_link["has_errors"])
        self.assertEqual(settings_link["badge"], 1)

    def test_get_menu_as_superuser_should_include_superuser(self):
        # Test Data
        url = reverse(f"{API_URL}:get_menu")
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        right_names = [link["name"] for link in data["right_links"]]
        self.assertIn("Superuser", right_names)

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
        right_names = [link["name"] for link in response.json()["right_links"]]
        self.assertIn("Overview", left_names)
        self.assertNotIn("Superuser", right_names)

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

    def test_get_user_settings_should_create_default_settings(self):
        # Test Data
        url = reverse(f"{API_URL}:get_user_settings")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(response.json()["disable_notifications"])
        self.assertTrue(UserSettings.objects.filter(user=self.user).exists())

    def test_update_user_settings_should_persist_notification_opt_out(self):
        # Test Data
        url = reverse(f"{API_URL}:update_user_settings")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.put(
            url,
            data='{"disable_notifications": true}',
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.json()["disable_notifications"])
        self.assertTrue(UserSettings.objects.get(user=self.user).disable_notifications)

    def test_user_settings_without_permission_should_return_forbidden(self):
        # Test Data
        url = reverse(f"{API_URL}:get_user_settings")
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_user_settings_without_permission_should_return_forbidden(
        self,
    ):
        # Test Data
        url = reverse(f"{API_URL}:update_user_settings")
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.put(
            url,
            data='{"disable_notifications": true}',
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_user_character_statuses_with_permission_should_return_character_statuses(
        self,
    ):
        # Test Data
        # AA Skillfarm
        from skillfarm.models.helpers.update_manager import CharacterUpdateSection
        from skillfarm.tests.testdata.skillfarm import (
            CharacterUpdateStatusFactory,
            SkillFarmAuditFactory,
        )

        audit = SkillFarmAuditFactory(
            user=self.user,
            character=self.user_character,
            active=True,
        )
        CharacterUpdateStatusFactory(
            owner=audit,
            section=CharacterUpdateSection.SKILLS,
            is_success=True,
            has_token_error=False,
            error_message="",
        )
        CharacterUpdateStatusFactory(
            owner=audit,
            section=CharacterUpdateSection.SKILLQUEUE,
            is_success=True,
            has_token_error=False,
            error_message="",
        )
        url = reverse(f"{API_URL}:get_user_character_statuses")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        char_status = data[0]
        self.assertEqual(char_status["character_id"], self.user_character.character_id)
        self.assertEqual(
            char_status["character_name"], self.user_character.character_name
        )
        self.assertEqual(char_status["status"], "ok")
        self.assertFalse(char_status["has_error"])
        self.assertTrue(char_status["is_active"])
        self.assertEqual(len(char_status["sections"]), 2)

    def test_get_user_character_statuses_with_error_should_return_has_error_flag(
        self,
    ):
        # Test Data
        # AA Skillfarm
        from skillfarm.models.helpers.update_manager import CharacterUpdateSection
        from skillfarm.tests.testdata.skillfarm import (
            CharacterUpdateStatusFactory,
            SkillFarmAuditFactory,
        )

        audit = SkillFarmAuditFactory(
            user=self.user,
            character=self.user_character,
            active=True,
        )
        CharacterUpdateStatusFactory(
            owner=audit,
            section=CharacterUpdateSection.SKILLS,
            is_success=False,
            has_token_error=False,
            error_message="ESI request timed out",
        )
        CharacterUpdateStatusFactory(
            owner=audit,
            section=CharacterUpdateSection.SKILLQUEUE,
            is_success=True,
            has_token_error=False,
            error_message="",
        )
        url = reverse(f"{API_URL}:get_user_character_statuses")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        char_status = data[0]
        self.assertEqual(char_status["status"], "error")
        self.assertTrue(char_status["has_error"])
        self.assertEqual(char_status["error_message"], "ESI request timed out")

    def test_get_user_character_statuses_without_permission_should_return_forbidden(
        self,
    ):
        # Test Data
        url = reverse(f"{API_URL}:get_user_character_statuses")
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
