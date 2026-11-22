# Third Party
from evesde_factory.allianceauth import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    UserFactory,
)

# Django
from django.utils import timezone

# AA Skillfarm
from skillfarm.models.helpers.update_manager import CharacterUpdateSection, UpdateStatus
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tests import AuthTestCase
from skillfarm.tests.testdata.skillfarm import (
    CharacterUpdateStatusFactory,
    SkillFarmAuditFactory,
    UserMainFactory,
)
from skillfarm.tests.testdata.utils import add_alt_character_to_user

MODULE_PATH = "skillfarm.managers.skillfarmaudit"


class TestCharacterAnnotateTotalUpdateStatus(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_should_be_ok(self):
        """
        Test should be OK when all sections are successful.
        """
        # given
        character = SkillFarmAuditFactory(user=self.user)
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            CharacterUpdateStatusFactory(
                owner=character,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # when/then
        self.assertEqual(
            character.skillfarm_update_status.get_status(), UpdateStatus.OK
        )

    def test_should_be_incomplete(self):
        """
        Test should be incomplete when no sections have been updated.
        """
        # given
        character = SkillFarmAuditFactory(user=self.user)
        # when/then
        self.assertEqual(
            character.skillfarm_update_status.get_status(), UpdateStatus.INCOMPLETE
        )

    def test_should_be_token_error(self):
        """
        Test should be token error when any section has a token error.
        """
        # given
        character = SkillFarmAuditFactory(user=self.user)
        CharacterUpdateStatusFactory(
            owner=character,
            section=CharacterUpdateSection.SKILLS,
            is_success=False,
            error_message="",
            has_token_error=True,
            last_run_at=timezone.now(),
            last_run_finished_at=timezone.now(),
            last_update_at=timezone.now(),
            last_update_finished_at=timezone.now(),
        )
        # when/then
        self.assertEqual(
            character.skillfarm_update_status.get_status(), UpdateStatus.TOKEN_ERROR
        )

    def test_should_be_disabled(self):
        """
        Test should be disabled when character is inactive.
        """
        character = SkillFarmAuditFactory(user=self.user, active=False)
        # given
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            CharacterUpdateStatusFactory(
                owner=character,
                section=section,
                is_success=True,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # when/then
        self.assertEqual(
            character.skillfarm_update_status.get_status(), UpdateStatus.DISABLED
        )

    def test_should_be_error(self):
        """
        Test should be error when any sections have errors.
        """
        # given
        character = SkillFarmAuditFactory(user=self.user)
        sections = CharacterUpdateSection.get_sections()
        for section in sections:
            CharacterUpdateStatusFactory(
                owner=character,
                section=section,
                is_success=False,
                error_message="",
                has_token_error=False,
                last_run_at=timezone.now(),
                last_run_finished_at=timezone.now(),
                last_update_at=timezone.now(),
                last_update_finished_at=timezone.now(),
            )

        # when/then
        self.assertEqual(
            character.skillfarm_update_status.get_status(), UpdateStatus.ERROR
        )


class TestSkillfarmAuditVisibleTo(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_should_return_audit(self):
        # given
        character = SkillFarmAuditFactory(user=self.user)
        # when
        qs = SkillFarmAudit.objects.visible_to(self.user)
        # then
        self.assertEqual(list(qs), [character])

    def test_should_return_empty_for_other_user(self):
        # given
        other_user = UserMainFactory()
        SkillFarmAuditFactory(user=self.user)
        # when
        qs = SkillFarmAudit.objects.visible_to(other_user)
        # then
        self.assertEqual(list(qs), [])

    def test_should_return_multiple_audits_for_user_with_multiple_characters(self):
        # given
        character1 = SkillFarmAuditFactory(user=self.user)
        # Add an alt character to the user
        eve_character = EveCharacterFactory()
        character2 = SkillFarmAuditFactory(user=self.user, character=eve_character)
        add_alt_character_to_user(
            user=self.user, character_id=character2.character.character_id
        )
        # when
        qs = SkillFarmAudit.objects.visible_to(self.user)
        # then
        self.assertCountEqual(list(qs), [character1, character2])

    def test_should_return_all_characters(self):
        # given
        other_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        character = SkillFarmAuditFactory(user=self.user)
        character2 = SkillFarmAuditFactory(user=other_user)
        # when
        qs = SkillFarmAudit.objects.visible_to(other_user)
        # then
        self.assertEqual(list(qs), [character, character2])


class TestSkillfarmAuditOwnedBy(AuthTestCase):
    def test_should_return_only_own_audits(self):
        # Test Data
        own_audit = SkillFarmAuditFactory(user=self.user)
        SkillFarmAuditFactory(user=UserMainFactory())

        # Test Action
        qs = SkillFarmAudit.objects.owned_by(self.user)

        # Expected Result
        self.assertEqual(list(qs), [own_audit])

    def test_should_return_alt_audits_of_user(self):
        # Test Data
        main_audit = SkillFarmAuditFactory(user=self.user)
        alt = EveCharacterFactory()
        add_alt_character_to_user(user=self.user, character_id=alt.character_id)
        alt_audit = SkillFarmAuditFactory(user=self.user, character=alt)

        # Test Action
        qs = SkillFarmAudit.objects.owned_by(self.user)

        # Expected Result
        self.assertCountEqual(list(qs), [main_audit, alt_audit])

    def test_should_not_return_all_audits_for_admin(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        SkillFarmAuditFactory(user=self.user)
        admin_audit = SkillFarmAuditFactory(user=admin_user)

        # Test Action
        qs = SkillFarmAudit.objects.owned_by(admin_user)

        # Expected Result
        self.assertEqual(list(qs), [admin_audit])


class TestSkillfarmAuditCorpAccess(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.corp = EveCorporationInfoFactory(
            corporation_id=98_000_000, corporation_name="Test Corporation"
        )

    def test_visible_to_with_corp_access_should_return_audits_of_same_corporation(
        self,
    ):
        # Test Data
        corp_char = EveCharacterFactory(corporation=self.corp)
        corp_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.corp_access"],
            main_character__character=corp_char,
        )
        colleague_char = EveCharacterFactory(corporation=self.corp)
        colleague = UserMainFactory(main_character__character=colleague_char)
        colleague_audit = SkillFarmAuditFactory(user=colleague)
        SkillFarmAuditFactory(user=UserMainFactory())

        # Test Action
        qs = SkillFarmAudit.objects.visible_to(corp_user)

        # Expected Result
        self.assertEqual(list(qs), [colleague_audit])


class TestSkillfarmAuditAccessRules(AuthTestCase):
    """Each access rule of `visible_to` and `manage_to`; they differ only for `corp_access`."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.corp = EveCorporationInfoFactory()
        cls.own_audit = SkillFarmAuditFactory(user=cls.user)
        cls.colleague = UserMainFactory(
            main_character__character=EveCharacterFactory(corporation=cls.corp)
        )
        cls.colleague_audit = SkillFarmAuditFactory(user=cls.colleague)
        cls.foreign_audit = SkillFarmAuditFactory(user=UserMainFactory())

    def _results(self, user):
        """Return the audits of `visible_to` and `manage_to` for the user."""
        return {
            "visible_to": list(SkillFarmAudit.objects.visible_to(user)),
            "manage_to": list(SkillFarmAudit.objects.manage_to(user)),
        }

    def _corp_user(self):
        return UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.corp_access"],
            main_character__character=EveCharacterFactory(corporation=self.corp),
        )

    def test_admin_access_should_return_all_audits(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )

        # Test Action
        for method, audits in self._results(admin_user).items():
            # Expected Result
            with self.subTest(method=method):
                self.assertCountEqual(
                    audits, [self.own_audit, self.colleague_audit, self.foreign_audit]
                )

    def test_admin_access_without_main_character_should_return_all_audits(self):
        # Test Data
        admin_user = UserFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )

        # Test Action
        for method, audits in self._results(admin_user).items():
            # Expected Result
            with self.subTest(method=method):
                self.assertCountEqual(
                    audits, [self.own_audit, self.colleague_audit, self.foreign_audit]
                )

    def test_corp_access_should_see_but_not_manage_audits_of_same_corporation(self):
        # Test Data
        corp_user = self._corp_user()

        # Test Action
        results = self._results(corp_user)

        # Expected Result
        self.assertEqual(results["visible_to"], [self.colleague_audit])
        self.assertEqual(results["manage_to"], [])

    def test_corp_access_should_manage_only_own_audits(self):
        # Test Data
        corp_user = self._corp_user()
        own_audit = SkillFarmAuditFactory(user=corp_user)
        alt = EveCharacterFactory()
        add_alt_character_to_user(user=corp_user, character_id=alt.character_id)
        alt_audit = SkillFarmAuditFactory(user=corp_user, character=alt)

        # Test Action
        results = self._results(corp_user)

        # Expected Result
        self.assertCountEqual(
            results["visible_to"], [self.colleague_audit, own_audit, alt_audit]
        )
        self.assertCountEqual(results["manage_to"], [own_audit, alt_audit])

    def test_own_character_should_return_only_own_audits(self):
        # Test Action
        for method, audits in self._results(self.user).items():
            # Expected Result
            with self.subTest(method=method):
                self.assertEqual(audits, [self.own_audit])

    def test_same_corporation_without_corp_access_should_return_only_own_audits(self):
        # Test Action
        for method, audits in self._results(self.colleague).items():
            # Expected Result
            with self.subTest(method=method):
                self.assertEqual(audits, [self.colleague_audit])

    def test_foreign_character_should_return_nothing(self):
        # Test Data
        other_user = UserMainFactory()

        # Test Action
        for method, audits in self._results(other_user).items():
            # Expected Result
            with self.subTest(method=method):
                self.assertEqual(audits, [])

    def test_user_without_main_character_should_return_nothing(self):
        # Test Data
        for permissions in (
            ["skillfarm.basic_access"],
            ["skillfarm.basic_access", "skillfarm.corp_access"],
        ):
            user = UserFactory(permissions__=permissions)
            alt = EveCharacterFactory(corporation=self.corp)
            add_alt_character_to_user(user=user, character_id=alt.character_id)
            SkillFarmAuditFactory(user=user, character=alt)

            # Test Action
            for method, audits in self._results(user).items():
                # Expected Result
                with self.subTest(method=method, permissions=permissions):
                    self.assertEqual(audits, [])

    def test_superuser_should_return_all_audits(self):
        """Superusers pass every `has_perm` check, so `admin_access` applies."""
        # Test Action
        for method, audits in self._results(self.superuser).items():
            # Expected Result
            with self.subTest(method=method):
                self.assertCountEqual(
                    audits, [self.own_audit, self.colleague_audit, self.foreign_audit]
                )

    def test_owned_by_should_ignore_main_character_and_permissions(self):
        # Test Data
        user = UserFactory(permissions__=["skillfarm.basic_access"])
        alt = EveCharacterFactory()
        add_alt_character_to_user(user=user, character_id=alt.character_id)
        alt_audit = SkillFarmAuditFactory(user=user, character=alt)

        # Test Action
        qs = SkillFarmAudit.objects.owned_by(user)

        # Expected Result
        self.assertEqual(list(qs), [alt_audit])

    def test_access_methods_should_work_on_filtered_queryset(self):
        # Test Action
        qs = SkillFarmAudit.objects.filter(pk=self.foreign_audit.pk)

        # Expected Result
        self.assertEqual(list(qs.visible_to(self.user)), [])
        self.assertEqual(list(qs.manage_to(self.user)), [])
        self.assertEqual(list(qs.owned_by(self.user)), [])


class TestSkillfarmFilterMethods(AuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_filter_by_schema_training_status_active_should_return_active(self):
        # Test Data
        # AA Skillfarm
        from skillfarm.api.schema import CharacterFilter

        char_active = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(),
            is_training=True,
        )
        char_paused = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(),
            is_training=False,
        )
        filters = CharacterFilter(training_status="training")

        # Test Action
        qs = SkillFarmAudit.objects.filter(
            id__in=[char_active.id, char_paused.id]
        ).filter_by_schema(filters)

        # Expected Result
        self.assertIn(char_active, qs)
        self.assertNotIn(char_paused, qs)

    def test_filter_by_schema_training_status_paused_should_return_paused(self):
        # Test Data
        # AA Skillfarm
        from skillfarm.api.schema import CharacterFilter

        char_active = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(),
            is_training=True,
        )
        char_paused = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(),
            is_training=False,
        )
        filters = CharacterFilter(training_status="paused")

        # Test Action
        qs = SkillFarmAudit.objects.filter(
            id__in=[char_active.id, char_paused.id]
        ).filter_by_schema(filters)

        # Expected Result
        self.assertIn(char_paused, qs)
        self.assertNotIn(char_active, qs)

    def test_filter_by_schema_extraction_status_pending_should_filter_correctly(self):
        # Test Data
        # AA Skillfarm
        from skillfarm.api.schema import CharacterFilter

        char_pending = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(),
            extractions_ready_count=2,
            extraction_acknowledged=False,
        )
        char_ack = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(),
            extractions_ready_count=2,
            extraction_acknowledged=True,
        )
        char_none = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(),
            extractions_ready_count=0,
            extraction_acknowledged=False,
        )
        filters = CharacterFilter(extraction_status="pending")

        # Test Action
        qs = SkillFarmAudit.objects.filter(
            id__in=[char_pending.id, char_ack.id, char_none.id]
        ).filter_by_schema(filters)

        # Expected Result
        self.assertIn(char_pending, qs)
        self.assertNotIn(char_ack, qs)
        self.assertNotIn(char_none, qs)

    def test_filter_by_schema_extraction_status_acknowledged_should_filter_correctly(
        self,
    ):
        # Test Data
        # AA Skillfarm
        from skillfarm.api.schema import CharacterFilter

        char_pending = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(),
            extractions_ready_count=2,
            extraction_acknowledged=False,
        )
        char_ack = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(),
            extractions_ready_count=2,
            extraction_acknowledged=True,
        )
        filters = CharacterFilter(extraction_status="acknowledged")

        # Test Action
        qs = SkillFarmAudit.objects.filter(
            id__in=[char_pending.id, char_ack.id]
        ).filter_by_schema(filters)

        # Expected Result
        self.assertIn(char_ack, qs)
        self.assertNotIn(char_pending, qs)

    def test_filter_by_schema_search_should_match_character_name(self):
        # Test Data
        # AA Skillfarm
        from skillfarm.api.schema import CharacterFilter

        char1 = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(character_name="Alpha Pilot Special"),
        )
        char2 = SkillFarmAuditFactory(
            user=self.user,
            character=EveCharacterFactory(character_name="Bravo Miner"),
        )
        filters = CharacterFilter(search="Special")

        # Test Action
        qs = SkillFarmAudit.objects.filter(
            id__in=[char1.id, char2.id]
        ).filter_by_schema(filters)

        # Expected Result
        self.assertIn(char1, qs)
        self.assertNotIn(char2, qs)
