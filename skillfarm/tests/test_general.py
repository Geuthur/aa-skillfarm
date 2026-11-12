"""Tests for the permission definitions and rules in General."""

# Standard Library
import re
from pathlib import Path

# Third Party
from evesde_factory.allianceauth import EveCharacterFactory, EveCorporationInfoFactory

# AA Skillfarm
import skillfarm
from skillfarm.models.general import General
from skillfarm.tests import AuthTestCase
from skillfarm.tests.testdata.skillfarm import UserMainFactory

APP_LABEL = "skillfarm"
# Permission strings like "<app_label>.<codename>" in quotes, any app label
PERMISSION_PATTERN = re.compile(r"[\"']([A-Za-z0-9_]+)\.([A-Za-z0-9_]*_access)[\"']")
# Files whose permission strings are checked: code and templates, not tests
SUFFIXES = (".py", ".html", ".txt")
IGNORED_PARTS = ("tests", "migrations")


class TestGeneralPermissions(AuthTestCase):
    def test_codenames_should_stay_unchanged(self):
        self.assertEqual(
            [codename for codename, _ in General._meta.permissions],
            ["basic_access", "corp_access", "admin_access"],
        )

    def test_used_permission_strings_should_exist_in_general(self):
        """Every permission string used in code and templates is defined in General.Meta.permissions."""
        defined = {f"{APP_LABEL}.{c}" for c, _ in General._meta.permissions}
        used: dict[str, set[str]] = {}
        root = Path(skillfarm.__file__).parent

        for path in root.rglob("*"):
            relative = path.relative_to(root)
            if path.suffix not in SUFFIXES or any(
                part in IGNORED_PARTS for part in relative.parts
            ):
                continue
            for label, codename in PERMISSION_PATTERN.findall(path.read_text("utf-8")):
                used.setdefault(f"{label}.{codename}", set()).add(str(relative))

        self.assertTrue(used, "No permission strings found, pattern is broken.")
        unknown = {c: sorted(f) for c, f in used.items() if c not in defined}
        self.assertEqual(unknown, {})


class TestGeneralManager(AuthTestCase):
    def test_has_management_access_should_be_true_for_admin_or_corp_access(self):
        # Test Data
        admin = UserMainFactory(permissions__=["skillfarm.admin_access"])
        corp = UserMainFactory(permissions__=["skillfarm.corp_access"])
        basic = UserMainFactory(permissions__=["skillfarm.basic_access"])

        # Test Action
        results = [
            General.objects.has_management_access(user) for user in (admin, corp, basic)
        ]

        # Expected Result
        self.assertEqual(results, [True, True, False])

    def test_has_basic_and_superuser_access(self):
        # Test Data
        basic = UserMainFactory(permissions__=["skillfarm.basic_access"])
        other = UserMainFactory(permissions__=["skillfarm.corp_access"])

        # Expected Result
        self.assertTrue(General.objects.has_basic_access(basic))
        self.assertFalse(General.objects.has_basic_access(other))
        self.assertTrue(General.objects.has_superuser_access(self.superuser))
        self.assertFalse(General.objects.has_superuser_access(basic))

    def test_has_administration_and_corporation_access(self):
        # Test Data
        admin = UserMainFactory(permissions__=["skillfarm.admin_access"])
        corp = UserMainFactory(permissions__=["skillfarm.corp_access"])

        # Expected Result
        self.assertTrue(General.objects.has_admin_access(admin))
        self.assertFalse(General.objects.has_admin_access(corp))
        self.assertTrue(General.objects.has_corporation_access(corp))
        self.assertFalse(General.objects.has_corporation_access(admin))

    def test_get_corporation_scope_should_return_all_for_admin_access(self):
        # Test Data
        user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )

        # Test Action
        result = General.objects.get_corporation_scope(user)

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
        result = General.objects.get_corporation_scope(user)

        # Expected Result
        self.assertEqual(result, (True, False, corporation.corporation_id))

    def test_get_corporation_scope_should_deny_without_management_permission(self):
        # Test Data
        user = UserMainFactory(permissions__=["skillfarm.basic_access"])

        # Test Action
        result = General.objects.get_corporation_scope(user)

        # Expected Result
        self.assertEqual(result, (False, False, None))

    def test_get_corporation_scope_should_deny_without_basic_access(self):
        # Test Data
        user = UserMainFactory(permissions__=["skillfarm.corp_access"])

        # Test Action
        result = General.objects.get_corporation_scope(user)

        # Expected Result
        self.assertEqual(result, (False, False, None))
