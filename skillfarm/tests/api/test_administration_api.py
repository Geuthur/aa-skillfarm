# Standard Library
from http import HTTPStatus
from unittest.mock import patch

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
)
from skillfarm.tests.testdata.skillfarm import SkillFarmAuditFactory, UserMainFactory

API_URL = "skillfarm:api"
TASK_PATH = "skillfarm.tasks"


class TestAdministrationApiEndpoints(SkillFarmTestCase):
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

    def test_get_menu_should_include_administration_link_for_superuser(self):
        # Test Data
        url = reverse(f"{API_URL}:get_menu")
        self.client.force_login(self.superuser)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        right_links = data.get("right_links", [])
        administration_link = next(
            (link for link in right_links if link["name"] == "Administration"), None
        )
        self.assertIsNotNone(administration_link)
        self.assertEqual(administration_link["link"], "/administration/")
        self.assertFalse(administration_link["is_external"])

    def test_get_menu_should_not_include_administration_link_for_regular_user(self):
        # Test Data
        url = reverse(f"{API_URL}:get_menu")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        right_links = data.get("right_links", [])
        administration_link = next(
            (link for link in right_links if link["name"] == "Administration"), None
        )
        self.assertIsNone(administration_link)

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

    def test_list_all_audits_as_admin_access_user_should_return_all_audits(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        url = reverse(f"{API_URL}:list_all_audits")
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        found = any(
            item["character_id"] == self.audit.character.character_id
            for item in response.json()
        )
        self.assertTrue(found)

    def test_list_all_audits_as_basic_access_user_should_return_forbidden(self):
        # Test Data
        url = reverse(f"{API_URL}:list_all_audits")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(
            response.json()["error"], "Administration permission required."
        )

    def test_list_all_audits_as_user_without_permission_should_return_forbidden(self):
        # Test Data
        url = reverse(f"{API_URL}:list_all_audits")
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @patch(f"{TASK_PATH}.update_character.apply_async")
    def test_trigger_audit_update_as_admin_without_force_should_queue_task(
        self, mock_apply_async
    ):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        url = reverse(
            f"{API_URL}:trigger_audit_update",
            kwargs={"character_id": self.audit.character.character_id},
        )
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.post(
            url, data={"force_refresh": False}, content_type="application/json"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_apply_async.assert_called_once_with(
            args=[self.audit.pk], kwargs={"force_refresh": False}, priority=7
        )

    @patch(f"{TASK_PATH}.update_character.apply_async")
    def test_trigger_audit_update_as_admin_with_force_should_return_forbidden(
        self, mock_apply_async
    ):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        url = reverse(
            f"{API_URL}:trigger_audit_update",
            kwargs={"character_id": self.audit.character.character_id},
        )
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.post(
            url, data={"force_refresh": True}, content_type="application/json"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.json()["error"], "Superuser permission required.")
        mock_apply_async.assert_not_called()

    def test_inspect_audit_as_admin_access_user_should_return_character_detail(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        url = reverse(
            f"{API_URL}:inspect_audit",
            kwargs={"character_id": self.audit.character.character_id},
        )
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_delete_audit_as_admin_access_user_should_return_forbidden(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        url = reverse(
            f"{API_URL}:delete_audit",
            kwargs={"character_id": self.audit.character.character_id},
        )
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(
            SkillFarmAudit.objects.filter(
                character__character_id=self.audit.character.character_id
            ).exists()
        )

    def test_get_admin_stats_as_admin_access_user_should_return_stats(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        url = reverse(f"{API_URL}:get_admin_stats")
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertGreaterEqual(response.json()["total_characters"], 1)

    @patch(f"{TASK_PATH}.update_all_skillfarm.apply_async")
    def test_trigger_update_all_as_admin_access_user_should_return_forbidden(
        self, mock_apply_async
    ):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        url = reverse(f"{API_URL}:trigger_update_all")
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.post(
            url, data={"force_refresh": False}, content_type="application/json"
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        mock_apply_async.assert_not_called()

    @patch(f"{TASK_PATH}.update_all_prices.apply_async")
    def test_trigger_update_prices_as_admin_access_user_should_return_forbidden(
        self, mock_apply_async
    ):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        url = reverse(f"{API_URL}:trigger_update_prices")
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.post(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        mock_apply_async.assert_not_called()


class TestAdministrationCorporationsApi(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_corp = EveCorporationInfoFactory(corporation_name="Other Corporation")

        # Registered character in the own corporation
        cls.registered_user = UserMainFactory(
            main_character__character=EveCharacterFactory(
                character_name="Registered Pilot", corporation=cls.corp
            )
        )
        cls.registered_audit = SkillFarmAuditFactory(user=cls.registered_user)
        # Unregistered characters in both corporations
        cls.unreg_zulu = EveCharacterFactory(
            character_name="Zulu Pilot", corporation=cls.corp
        )
        cls.unreg_alpha = EveCharacterFactory(
            character_name="Alpha Pilot", corporation=cls.corp
        )
        cls.unreg_other = EveCharacterFactory(
            character_name="Other Pilot", corporation=cls.other_corp
        )

        cls.corp_user = UserMainFactory(
            main_character__character=EveCharacterFactory(corporation=cls.corp),
            permissions__=["skillfarm.basic_access", "skillfarm.corp_access"],
        )
        cls.admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )

    def _list_url(self):
        return reverse(f"{API_URL}:list_corporations")

    def _unregistered_url(self, corporation_id):
        return reverse(
            f"{API_URL}:list_corporation_unregistered",
            kwargs={"corporation_id": corporation_id},
        )

    def test_list_corporations_as_corp_access_should_return_only_own_corporation(self):
        # Test Data
        self.client.force_login(self.corp_user)

        # Test Action
        response = self.client.get(self._list_url())

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(
            [c["corporation_id"] for c in data], [self.corp.corporation_id]
        )
        self.assertEqual(data[0]["registered_count"], 1)
        # corp_user main, Alpha, Zulu
        self.assertEqual(data[0]["unregistered_count"], 3)

    def test_list_corporations_as_admin_access_should_return_all_corporations(self):
        # Test Data
        self.client.force_login(self.admin_user)

        # Test Action
        response = self.client.get(self._list_url())

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        ids = {c["corporation_id"] for c in response.json()}
        self.assertIn(self.corp.corporation_id, ids)
        self.assertIn(self.other_corp.corporation_id, ids)

    def test_list_corporations_should_exclude_npc_corporations(self):
        # Test Data
        npc_corp = EveCorporationInfoFactory(
            corporation_id=1_000_001, corporation_name="NPC Corporation"
        )
        EveCharacterFactory(character_name="NPC Pilot", corporation=npc_corp)
        self.client.force_login(self.admin_user)

        # Test Action
        response = self.client.get(self._list_url())

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        ids = {c["corporation_id"] for c in response.json()}
        self.assertNotIn(npc_corp.corporation_id, ids)
        self.assertIn(self.corp.corporation_id, ids)

    def test_list_unregistered_for_npc_corporation_should_return_not_found(self):
        # Test Data
        npc_corp = EveCorporationInfoFactory(
            corporation_id=1_000_002, corporation_name="NPC Corporation"
        )
        EveCharacterFactory(character_name="NPC Pilot", corporation=npc_corp)
        self.client.force_login(self.admin_user)

        # Test Action
        response = self.client.get(self._unregistered_url(npc_corp.corporation_id))

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_list_corporations_without_management_permission_should_return_forbidden(
        self,
    ):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(self._list_url())

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_list_unregistered_as_corp_access_should_return_sorted_unregistered_only(
        self,
    ):
        # Test Data
        self.client.force_login(self.corp_user)

        # Test Action
        response = self.client.get(self._unregistered_url(self.corp.corporation_id))

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        items = response.json()["items"]
        names = [i["name"] for i in items]
        self.assertEqual(names, sorted(names))
        self.assertIn("Alpha Pilot", names)
        self.assertIn("Zulu Pilot", names)
        self.assertNotIn("Registered Pilot", names)
        self.assertNotIn("Other Pilot", names)
        self.assertEqual(items[0]["subtitle"], self.corp.corporation_name)

    def test_list_unregistered_as_corp_access_for_other_corp_should_return_forbidden(
        self,
    ):
        # Test Data
        self.client.force_login(self.corp_user)

        # Test Action
        response = self.client.get(
            self._unregistered_url(self.other_corp.corporation_id)
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_list_unregistered_as_admin_access_should_return_any_corporation(self):
        # Test Data
        self.client.force_login(self.admin_user)

        # Test Action
        response = self.client.get(
            self._unregistered_url(self.other_corp.corporation_id)
        )

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        names = [i["name"] for i in response.json()["items"]]
        self.assertEqual(names, ["Other Pilot"])

    def test_list_unregistered_without_permission_should_return_forbidden(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(self._unregistered_url(self.corp.corporation_id))

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_list_unregistered_for_unknown_corporation_should_return_not_found(self):
        # Test Data
        self.client.force_login(self.admin_user)

        # Test Action
        response = self.client.get(self._unregistered_url(1))

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_menu_as_corp_access_user_should_include_administration(self):
        # Test Data
        self.client.force_login(self.corp_user)

        # Test Action
        response = self.client.get(reverse(f"{API_URL}:get_menu"))

        # Expected Result
        names = [link["name"] for link in response.json()["right_links"]]
        self.assertIn("Administration", names)

    def test_list_all_audits_as_corp_access_should_still_return_forbidden(self):
        # Test Data
        self.client.force_login(self.corp_user)

        # Test Action
        response = self.client.get(reverse(f"{API_URL}:list_all_audits"))

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
