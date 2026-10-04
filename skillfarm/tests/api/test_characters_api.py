# Standard Library
import json
from http import HTTPStatus

# Django
from django.urls import reverse

# AA Skillfarm
from skillfarm.models.skillfarmaudit import SkillFarmAudit, SkillFarmSetup
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.factory import EveCharacterFactory
from skillfarm.tests.testdata.skillfarm import (
    CharacterSkillqueueEntryFactory,
    SkillFarmAuditFactory,
    SkillFarmSetupFactory,
    UserMainFactory,
)
from skillfarm.tests.testdata.utils import add_alt_character_to_user

API_URL = "skillfarm:api"


class TestCharactersApiEndpoints(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.audit = SkillFarmAuditFactory(
            user=cls.user,
            character=cls.user_character,
            is_training=True,
            extractions_ready_count=2,
            extraction_acknowledged=False,
        )
        cls.skillsetup = SkillFarmSetupFactory(
            character=cls.audit, skillset=["Cybernetics"]
        )

    def setUp(self):
        super().setUp()
        self.audit.refresh_from_db()
        self.audit.is_training = True
        self.audit.extractions_ready_count = 2
        self.audit.extraction_acknowledged = False
        self.audit.queue_paused_acknowledged = False
        self.audit.notification = False
        self.audit.save()
        self.skillsetup.refresh_from_db()
        self.skillsetup.skillset = ["Cybernetics"]
        self.skillsetup.save()

    def test_list_characters_should_return_character_list_and_counters(self):
        # Test Data
        url = reverse(f"{API_URL}:list_characters")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertIn("characters", data)
        self.assertEqual(data["total_count"], 1)
        self.assertEqual(data["pending_extractions_count"], 1)
        self.assertEqual(data["acknowledged_extractions_count"], 0)
        self.assertEqual(len(data["characters"]), 1)
        self.assertEqual(
            data["characters"][0]["character_name"],
            self.user_character.character_name,
        )

    def test_list_characters_as_admin_should_only_return_own_characters(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        admin_audit = SkillFarmAuditFactory(user=admin_user)
        url = reverse(f"{API_URL}:list_characters")
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(data["total_count"], 1)
        self.assertEqual(
            [char["character_id"] for char in data["characters"]],
            [admin_audit.character.character_id],
        )

    def test_list_characters_with_paused_filter_should_filter_results(self):
        # Test Data
        url = reverse(f"{API_URL}:list_characters")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(f"{url}?training_status=paused")

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(len(data["characters"]), 0)

    def test_list_characters_without_permission_should_return_forbidden(self):
        # Test Data
        url = reverse(f"{API_URL}:list_characters")
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_character_detail_should_return_detail_data(self):
        # Test Data
        url = reverse(
            f"{API_URL}:get_character_detail",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertEqual(
            data["character"]["character_id"], self.user_character.character_id
        )
        self.assertIn("skillqueue", data)
        self.assertIn("farmed_skills", data)
        self.assertEqual(data["configured_skillset"], ["Cybernetics"])

    def test_get_character_detail_with_null_dates_should_return_boolean_is_extractable(
        self,
    ):
        # Test Data
        CharacterSkillqueueEntryFactory(
            character=self.audit,
            finished_level=5,
            start_date=None,
            finish_date=None,
        )
        url = reverse(
            f"{API_URL}:get_character_detail",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertTrue(len(data["skillqueue"]) > 0)
        for entry in data["skillqueue"]:
            self.assertIsInstance(entry["is_extractable"], bool)
            self.assertIsInstance(entry["is_active"], bool)

    def test_get_character_detail_nonexistent_should_return_404(self):
        # Test Data
        url = reverse(
            f"{API_URL}:get_character_detail",
            kwargs={"character_id": 99999999},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_acknowledge_extractions_should_mark_extractions_as_reviewed(self):
        # Test Data
        self.audit.extraction_acknowledged = False
        self.audit.save(update_fields=["extraction_acknowledged"])
        url = reverse(
            f"{API_URL}:acknowledge_extractions",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertTrue(data["success"])
        self.audit.refresh_from_db()
        self.assertTrue(self.audit.extraction_acknowledged)
        self.assertIsNotNone(self.audit.extraction_acknowledged_at)
        self.assertEqual(self.audit.extraction_acknowledged_by, self.user)

    def test_acknowledge_paused_should_mark_queue_as_acknowledged(self):
        # Test Data
        self.audit.queue_paused_acknowledged = False
        self.audit.save(update_fields=["queue_paused_acknowledged"])
        url = reverse(
            f"{API_URL}:acknowledge_paused",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()
        self.assertTrue(data["success"])
        self.audit.refresh_from_db()
        self.assertTrue(self.audit.queue_paused_acknowledged)

    def test_toggle_notification_should_invert_notification_setting(self):
        # Test Data
        initial_val = self.audit.notification
        url = reverse(
            f"{API_URL}:toggle_notification",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.notification, not initial_val)

    def test_get_and_update_skillsetup_should_modify_skillset(self):
        # Test Data
        get_url = reverse(
            f"{API_URL}:get_skillsetup",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action 1: Get setup
        get_res = self.client.get(get_url)
        self.assertEqual(get_res.status_code, HTTPStatus.OK)

        # Test Action 2: Update setup
        post_url = reverse(
            f"{API_URL}:update_skillsetup",
            kwargs={"character_id": self.user_character.character_id},
        )
        post_res = self.client.post(
            post_url,
            data=json.dumps(
                {"selected_skills": ["Cybernetics", "Infomorph Psychology"]}
            ),
            content_type="application/json",
        )

        # Expected Result
        self.assertEqual(post_res.status_code, HTTPStatus.OK)
        setup = SkillFarmSetup.objects.get(character=self.audit)
        self.assertEqual(setup.skillset, ["Cybernetics", "Infomorph Psychology"])

    def test_acknowledge_all_extractions_should_bulk_update_audits(self):
        # Test Data
        self.audit.extraction_acknowledged = False
        self.audit.extractions_ready_count = 3
        self.audit.save()
        url = reverse(f"{API_URL}:acknowledge_all_extractions")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.audit.refresh_from_db()
        self.assertTrue(self.audit.extraction_acknowledged)

    def test_delete_character_should_remove_audit_object(self):
        # Test Data
        extra_char = EveCharacterFactory()
        add_alt_character_to_user(user=self.user, character_id=extra_char.character_id)
        extra_audit = SkillFarmAuditFactory(user=self.user, character=extra_char)
        url = reverse(
            f"{API_URL}:delete_character",
            kwargs={"character_id": extra_char.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.delete(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(SkillFarmAudit.objects.filter(id=extra_audit.id).exists())

    def test_acknowledge_all_extractions_should_not_touch_foreign_audits(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        foreign_audit = SkillFarmAuditFactory(
            user=admin_user, extractions_ready_count=1, extraction_acknowledged=False
        )
        url = reverse(f"{API_URL}:acknowledge_all_extractions")
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
        foreign_audit.refresh_from_db()
        self.assertFalse(foreign_audit.extraction_acknowledged)

    def test_acknowledge_all_extractions_without_permission_should_return_forbidden(
        self,
    ):
        # Test Data
        url = reverse(f"{API_URL}:acknowledge_all_extractions")
        self.client.force_login(self.no_permission_user)

        # Test Action
        response = self.client.post(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_toggle_notification_of_foreign_character_should_return_forbidden(self):
        # Test Data
        foreign_audit = SkillFarmAuditFactory(user=UserMainFactory())
        url = reverse(
            f"{API_URL}:toggle_notification",
            kwargs={"character_id": foreign_audit.character.character_id},
        )
        self.client.force_login(self.user)

        # Test Action
        response = self.client.post(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_toggle_notification_of_foreign_character_as_admin_should_succeed(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        url = reverse(
            f"{API_URL}:toggle_notification",
            kwargs={"character_id": self.user_character.character_id},
        )
        self.client.force_login(admin_user)

        # Test Action
        response = self.client.post(url)

        # Expected Result
        self.assertEqual(response.status_code, HTTPStatus.OK)
