# Standard Library
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import EveCharacterFactory
from skillfarm.tests.testdata.skillfarm import SkillFarmAuditFactory, UserMainFactory
from skillfarm.tests.testdata.utils import add_alt_character_to_user

API_URL = "skillfarm:api"


class TestOverviewApiEndpoints(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        cls.audit = SkillFarmAuditFactory(
            user=cls.user,
            is_training=True,
            extractions_ready_count=1,
            extraction_acknowledged=False,
        )
        cls.alt = EveCharacterFactory()
        add_alt_character_to_user(user=cls.user, character_id=cls.alt.character_id)
        cls.alt_audit = SkillFarmAuditFactory(
            user=cls.user, character=cls.alt, is_training=False
        )
        cls.other_audit = SkillFarmAuditFactory(user=UserMainFactory())

    def test_get_overview_as_standard_user_should_return_forbidden(self):
        # Test Data
        url = reverse(f"{API_URL}:get_overview")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_overview_as_admin_should_group_characters_by_user(self):
        # Test Data
        url = reverse(f"{API_URL}:get_overview")
        self.client.force_login(self.admin_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        users = {entry["user_id"]: entry for entry in response.json()["users"]}
        self.assertEqual(len(users), 2)
        entry = users[self.user.id]
        self.assertEqual(entry["character_count"], 2)
        self.assertEqual(entry["training_count"], 1)
        self.assertEqual(entry["paused_count"], 1)
        self.assertEqual(entry["pending_extractions_count"], 1)
        self.assertEqual(
            entry["main_character_name"], self.user_character.character_name
        )

    def test_get_overview_as_corp_user_should_only_return_own_corporation(self):
        # Test Data
        corp_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.corp_access"],
            main_character__character=EveCharacterFactory(corporation=self.corp),
        )
        colleague = UserMainFactory(
            main_character__character=EveCharacterFactory(corporation=self.corp)
        )
        SkillFarmAuditFactory(user=colleague)
        url = reverse(f"{API_URL}:get_overview")
        self.client.force_login(corp_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        user_ids = [entry["user_id"] for entry in response.json()["users"]]
        self.assertEqual(user_ids, [colleague.id])

    def test_get_overview_user_should_return_characters_of_user(self):
        # Test Data
        url = reverse(f"{API_URL}:get_overview_user", kwargs={"user_id": self.user.id})
        self.client.force_login(self.admin_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["user"]["user_id"], self.user.id)
        self.assertEqual(data["total_count"], 2)
        self.assertCountEqual(
            [char["character_id"] for char in data["characters"]],
            [self.user_character.character_id, self.alt.character_id],
        )

    def test_get_overview_user_with_filter_should_filter_characters(self):
        # Test Data
        url = reverse(f"{API_URL}:get_overview_user", kwargs={"user_id": self.user.id})
        self.client.force_login(self.admin_user)

        # Test Action
        response = self.client.get(f"{url}?training_status=paused")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(
            [char["character_id"] for char in data["characters"]],
            [self.alt.character_id],
        )
        self.assertEqual(data["total_count"], 2)

    def test_get_overview_user_as_standard_user_should_return_forbidden(self):
        # Test Data
        url = reverse(f"{API_URL}:get_overview_user", kwargs={"user_id": self.user.id})
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_overview_user_unknown_should_return_not_found(self):
        # Test Data
        url = reverse(f"{API_URL}:get_overview_user", kwargs={"user_id": 99999999})
        self.client.force_login(self.admin_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
