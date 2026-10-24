# Third Party
from evesde_factory.allianceauth import EveCharacterFactory, EveCorporationInfoFactory

# Django
from django.contrib.auth.models import AnonymousUser

# AA Skillfarm
from skillfarm.models.general import General
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.skillfarm import UserMainFactory


class TestGeneralPermissions(SkillFarmTestCase):
    def test_get_perm_should_return_full_permission_string_for_enum(self):
        # Test Data
        perm = General.Permission.BASIC_ACCESS

        # Test Action
        result = General.get_perm(perm)

        # Expected Result
        self.assertEqual(result, "skillfarm.basic_access")

    def test_get_perm_should_return_full_permission_string_for_codename(self):
        # Test Data
        codename = "corp_access"

        # Test Action
        result = General.get_perm(codename)

        # Expected Result
        self.assertEqual(result, "skillfarm.corp_access")

    def test_meta_permissions_should_keep_existing_codenames(self):
        # Test Data
        expected = {"basic_access", "corp_access", "admin_access"}

        # Test Action
        codenames = {codename for codename, _ in General._meta.permissions}

        # Expected Result
        self.assertEqual(codenames, expected)

    def test_has_perm_should_return_true_for_user_with_permission(self):
        # Test Data
        user = UserMainFactory(permissions__=["skillfarm.basic_access"])

        # Test Action
        result = General.has_perm(user, General.Permission.BASIC_ACCESS)

        # Expected Result
        self.assertTrue(result)

    def test_has_perm_should_return_false_for_user_without_permission(self):
        # Test Data
        user = UserMainFactory(permissions__=["skillfarm.basic_access"])

        # Test Action
        result = General.has_perm(user, General.Permission.ADMIN_ACCESS)

        # Expected Result
        self.assertFalse(result)

    def test_has_perm_should_return_true_for_superuser(self):
        # Test Data
        user = self.superuser

        # Test Action
        result = General.has_perm(user, General.Permission.ADMIN_ACCESS)

        # Expected Result
        self.assertTrue(result)

    def test_has_perm_should_return_false_for_none_user(self):
        # Test Data
        user = None

        # Test Action
        result = General.has_perm(user, General.Permission.BASIC_ACCESS)

        # Expected Result
        self.assertFalse(result)

    def test_has_perm_should_return_false_for_anonymous_user(self):
        # Test Data
        user = AnonymousUser()

        # Test Action
        result = General.has_perm(user, General.Permission.BASIC_ACCESS)

        # Expected Result
        self.assertFalse(result)

    def test_has_any_perm_should_return_true_if_one_permission_matches(self):
        # Test Data
        user = UserMainFactory(permissions__=["skillfarm.corp_access"])

        # Test Action
        result = General.has_any_perm(
            user, General.Permission.ADMIN_ACCESS, General.Permission.CORP_ACCESS
        )

        # Expected Result
        self.assertTrue(result)

    def test_has_any_perm_should_return_false_if_no_permission_matches(self):
        # Test Data
        user = UserMainFactory(permissions__=["skillfarm.basic_access"])

        # Test Action
        result = General.has_any_perm(
            user, General.Permission.ADMIN_ACCESS, General.Permission.CORP_ACCESS
        )

        # Expected Result
        self.assertFalse(result)

    def test_has_any_perm_should_return_false_for_none_and_anonymous_user(self):
        # Test Data
        users = [None, AnonymousUser()]

        # Test Action
        results = [
            General.has_any_perm(user, General.Permission.BASIC_ACCESS)
            for user in users
        ]

        # Expected Result
        self.assertEqual(results, [False, False])

    def test_has_any_perm_should_return_true_for_superuser(self):
        # Test Data
        user = self.superuser

        # Test Action
        result = General.has_any_perm(user, General.Permission.CORP_ACCESS)

        # Expected Result
        self.assertTrue(result)

    def test_has_basic_access_should_reflect_basic_permission(self):
        # Test Data
        allowed = UserMainFactory(permissions__=["skillfarm.basic_access"])
        denied = UserMainFactory(permissions__=[])

        # Test Action
        results = [
            General.has_basic_access(allowed),
            General.has_basic_access(denied),
            General.has_basic_access(None),
            General.has_basic_access(AnonymousUser()),
        ]

        # Expected Result
        self.assertEqual(results, [True, False, False, False])

    def test_has_administration_access_should_reflect_admin_permission(self):
        # Test Data
        admin = UserMainFactory(permissions__=["skillfarm.admin_access"])
        corp = UserMainFactory(permissions__=["skillfarm.corp_access"])

        # Test Action
        results = [
            General.has_administration_access(admin),
            General.has_administration_access(corp),
            General.has_administration_access(self.superuser),
            General.has_administration_access(None),
        ]

        # Expected Result
        self.assertEqual(results, [True, False, True, False])

    def test_has_corporation_access_should_reflect_corp_permission(self):
        # Test Data
        corp = UserMainFactory(permissions__=["skillfarm.corp_access"])
        basic = UserMainFactory(permissions__=["skillfarm.basic_access"])

        # Test Action
        results = [
            General.has_corporation_access(corp),
            General.has_corporation_access(basic),
            General.has_corporation_access(None),
        ]

        # Expected Result
        self.assertEqual(results, [True, False, False])

    def test_has_management_access_should_be_true_for_admin_or_corp_access(self):
        # Test Data
        admin = UserMainFactory(permissions__=["skillfarm.admin_access"])
        corp = UserMainFactory(permissions__=["skillfarm.corp_access"])
        basic = UserMainFactory(permissions__=["skillfarm.basic_access"])

        # Test Action
        results = [
            General.has_management_access(admin),
            General.has_management_access(corp),
            General.has_management_access(basic),
            General.has_management_access(None),
        ]

        # Expected Result
        self.assertEqual(results, [True, True, False, False])

    def test_is_superuser_only_should_be_true_only_for_superuser(self):
        # Test Data
        admin = UserMainFactory(permissions__=["skillfarm.admin_access"])

        # Test Action
        results = [
            General.is_superuser_only(self.superuser),
            General.is_superuser_only(admin),
            General.is_superuser_only(AnonymousUser()),
            General.is_superuser_only(None),
        ]

        # Expected Result
        self.assertEqual(results, [True, False, False, False])

    def test_get_own_corporation_id_should_return_main_character_corporation(self):
        # Test Data
        corporation = EveCorporationInfoFactory()
        user = UserMainFactory(
            main_character__character=EveCharacterFactory(corporation=corporation)
        )

        # Test Action
        result = General.get_own_corporation_id(user)

        # Expected Result
        self.assertEqual(result, corporation.corporation_id)

    def test_get_own_corporation_id_should_return_none_without_user_or_main(self):
        # Test Data
        users = [None, AnonymousUser()]

        # Test Action
        results = [General.get_own_corporation_id(user) for user in users]

        # Expected Result
        self.assertEqual(results, [None, None])

    def test_get_corporation_scope_should_return_all_for_admin_access(self):
        # Test Data
        user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )

        # Test Action
        result = General.get_corporation_scope(user)

        # Expected Result
        self.assertEqual(result, (True, True, None))

    def test_get_corporation_scope_should_return_own_corporation_for_corp_access(
        self,
    ):
        # Test Data
        corporation = EveCorporationInfoFactory()
        user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.corp_access"],
            main_character__character=EveCharacterFactory(corporation=corporation),
        )

        # Test Action
        result = General.get_corporation_scope(user)

        # Expected Result
        self.assertEqual(result, (True, False, corporation.corporation_id))

    def test_get_corporation_scope_should_deny_without_management_permission(self):
        # Test Data
        user = UserMainFactory(permissions__=["skillfarm.basic_access"])

        # Test Action
        result = General.get_corporation_scope(user)

        # Expected Result
        self.assertEqual(result, (False, False, None))

    def test_get_corporation_scope_should_deny_without_basic_access(self):
        # Test Data
        user = UserMainFactory(permissions__=["skillfarm.corp_access"])

        # Test Action
        result = General.get_corporation_scope(user)

        # Expected Result
        self.assertEqual(result, (False, False, None))
