# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.models.helpers.update_manager import CharacterUpdateSection
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import (
    CharacterUpdateStatusFactory,
    SkillFarmAuditFactory,
    SkillFarmSetupFactory,
)

MODULE_PATH = "skillfarm.api.helpers."
API_URL = "skillfarm:api"


class TestApiEndpoints(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.audit = SkillFarmAuditFactory(user=cls.user)
        cls.update_status = CharacterUpdateStatusFactory(
            character=cls.audit, section=CharacterUpdateSection.SKILLS
        )
        cls.skillsetup = SkillFarmSetupFactory(character=cls.audit)

    def test_overview_api_endpoint_should_return_200_ok(self):
        """
        Test should return 200 OK for overview API endpoint.
        """
        # Test Data
        url = reverse(f"{API_URL}:get_character_overview")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_details_api_endpoint_should_return_200_ok(self):
        """
        Test should return 200 OK for details API endpoint.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:get_details",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_details_api_endpoint_should_return_403_forbidden(self):
        """
        Test should return 403 FORBIDDEN for details API endpoint.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:get_details",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_skillsetup_api_endpoint_should_return_200_ok(self):
        """
        Test should return 200 OK for skill setup API endpoint.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:get_skillsetup",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_skillsetup_api_endpoint_should_return_403_forbidden(self):
        """
        Test should return 403 FORBIDDEN for skill setup API endpoint.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:get_skillsetup",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_skillqueue_api_endpoint_should_return_200_ok(self):
        """
        Test should return 200 OK for skill queue API endpoint.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:get_skillqueue",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_skillqueue_api_endpoint_should_return_403_forbidden(self):
        """
        Test should return 403 FORBIDDEN for skill queue API endpoint.
        """
        # Test Data
        url = reverse(
            f"{API_URL}:get_skillqueue",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
