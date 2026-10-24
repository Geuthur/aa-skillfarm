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
