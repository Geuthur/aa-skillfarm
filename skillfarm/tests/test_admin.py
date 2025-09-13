# Django
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

# AA Skillfarm
from skillfarm.admin import SkillFarmAuditAdmin
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.skillfarm import create_skillfarm_character

MODULE_PATH = "skillfarm.admin."


class TestAdminView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.adminmodel = SkillFarmAuditAdmin(
            model=SkillFarmAudit, admin_site=AdminSite()
        )
        cls.character = create_skillfarm_character(1001)
        cls.user = cls.character.character.character_ownership.user

    def test_column_entity_pic(self):
        """Test if the entity pic column is displayed correctly"""
        self.assertEqual(
            self.adminmodel._entity_pic(self.character),
            '<img src="https://images.evetech.net/characters/1001/portrait?size=32" class="img-circle">',
        )

    def test_column_character(self):
        """Test if the character column is displayed correctly"""
        self.assertEqual(self.adminmodel._character__character_id(self.character), 1001)

    def test_column_character_name(self):
        """Test if the character name column is displayed correctly"""
        self.assertEqual(
            self.adminmodel._character__character_name(self.character), "Gneuten"
        )

    def test_has_add_permission(self):
        """Test if the user has the permission to add should be false"""
        self.assertFalse(self.adminmodel.has_add_permission(RequestFactory()))

    def test_has_change_permission(self):
        """Test if the user has the permission to change should be false"""
        self.assertFalse(self.adminmodel.has_change_permission(RequestFactory()))
