# AA Skillfarm
from skillfarm.api.helpers import core
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.skillfarm import SkillFarmAuditFactory, UserMainFactory

MODULE_PATH = "skillfarm.api.helpers."


class TestCoreHelpers(SkillFarmTestCase):
    """Test Core Helper Functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.skillfarm_audit = SkillFarmAuditFactory(user=cls.user)

    def test_get_skillfarm_character(self):
        """
        Test should return SkillFarmAudit.
        """
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        perm, skillfarm_character = core.get_skillfarm_character(
            request=request, character_id=self.skillfarm_audit.character.character_id
        )
        # then
        self.assertEqual(
            skillfarm_character.character.character_id,
            self.skillfarm_audit.character.character_id,
        )
        self.assertTrue(perm)  # Has Permission

    def test_get_skillfarm_character_no_permission(self):
        """
        Test should return SkillFarmAudit & No Permission.
        """
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        perm, skillfarm_character = core.get_skillfarm_character(
            request=request, character_id=self.superuser_character.character_id
        )
        # then
        self.assertFalse(perm)  # No permission
        self.assertIsNone(skillfarm_character)  # No SkillFarmAudit found

    def test_get_skillfarm_character_nonexistent(self):
        """
        Test should return None when SkillFarmAudit does not exist.
        """
        # given
        request = self.factory.get("/")
        request.user = self.user
        # when
        perm, skillfarm_character = core.get_skillfarm_character(
            request=request, character_id=999999999
        )
        # then
        self.assertFalse(perm)  # No permission
        self.assertIsNone(skillfarm_character)  # No SkillFarmAudit found

    def test_get_skillfarm_character_manage_should_deny_foreign_audit(self):
        # Test Data
        request = self.factory.get("/")
        request.user = self.user
        other_audit = SkillFarmAuditFactory(user=UserMainFactory())

        # Test Action
        perm, audit = core.get_skillfarm_character(
            request=request,
            character_id=other_audit.character.character_id,
            manage=True,
        )

        # Expected Result
        self.assertFalse(perm)
        self.assertEqual(audit, other_audit)

    def test_get_skillfarm_character_manage_should_allow_admin(self):
        # Test Data
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )
        request = self.factory.get("/")
        request.user = admin_user

        # Test Action
        perm, audit = core.get_skillfarm_character(
            request=request,
            character_id=self.skillfarm_audit.character.character_id,
            manage=True,
        )

        # Expected Result
        self.assertTrue(perm)
        self.assertEqual(audit, self.skillfarm_audit)

    def test_can_view_overview_should_be_false_for_standard_user(self):
        # Test Action / Expected Result
        self.assertFalse(core.can_view_overview(self.user))

    def test_can_view_overview_should_be_true_for_corp_and_admin_user(self):
        # Test Data
        corp_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.corp_access"]
        )
        admin_user = UserMainFactory(
            permissions__=["skillfarm.basic_access", "skillfarm.admin_access"]
        )

        # Test Action / Expected Result
        self.assertTrue(core.can_view_overview(corp_user))
        self.assertTrue(core.can_view_overview(admin_user))
        self.assertTrue(core.can_view_overview(self.superuser))

    def test_can_view_overview_should_be_false_without_basic_access(self):
        # Test Data
        user = UserMainFactory(permissions__=["skillfarm.corp_access"])

        # Test Action / Expected Result
        self.assertFalse(core.can_view_overview(user))
