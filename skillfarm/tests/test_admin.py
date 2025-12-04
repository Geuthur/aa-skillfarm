# Django
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

# AA Skillfarm
from skillfarm.admin import SkillFarmAuditAdmin
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.utils import create_skillfarm_character_from_user

MODULE_PATH = "skillfarm.admin."


class TestAdminView(SkillFarmTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.adminmodel = SkillFarmAuditAdmin(
            model=SkillFarmAudit, admin_site=AdminSite()
        )
        cls.skillfarm_audit = create_skillfarm_character_from_user(cls.user)

    def test_column_entity_pic(self):
        """
        Test should display the character portrait correctly.
        """
        self.assertEqual(
            self.adminmodel._entity_pic(self.skillfarm_audit),
            '<img src="https://images.evetech.net/characters/1001/portrait?size=32" class="img-circle">',
        )

    def test_column_character(self):
        """
        Test should display the character id correctly
        """
        self.assertEqual(
            self.adminmodel._character__character_id(self.skillfarm_audit), 1001
        )

    def test_column_character_name(self):
        """
        Test should display the character name correctly.
        """
        self.assertEqual(
            self.adminmodel._character__character_name(self.skillfarm_audit), "Gneuten"
        )

    def test_has_add_permission(self):
        """
        Test should disable adding SkillFarmAudit entries via admin.
        """
        self.assertFalse(self.adminmodel.has_add_permission(RequestFactory()))

    def test_has_change_permission(self):
        """
        Test should disable changing SkillFarmAudit entries via admin.
        """
        self.assertFalse(self.adminmodel.has_change_permission(RequestFactory()))
