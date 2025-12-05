# Django
from django.test import TestCase, modify_settings

# AA Skillfarm
from skillfarm.helpers.discord import (
    allianceauth_discordbot_installed,
    discordnotify_installed,
)


class TestModulesInstalled(TestCase):
    @modify_settings(INSTALLED_APPS={"remove": "aadiscordbot"})
    def test_allianceauth_discordbot_installed_should_return_false(self):
        """
        Test should return False if aadiscordbot is not installed.
        """
        self.assertFalse(allianceauth_discordbot_installed())

    @modify_settings(INSTALLED_APPS={"append": "aadiscordbot"})
    def test_allianceauth_discordbot_installed_should_return_true(self):
        """
        Test should return True if aadiscordbot is installed.
        """
        self.assertTrue(allianceauth_discordbot_installed())

    @modify_settings(INSTALLED_APPS={"remove": "discordnotify"})
    def test_aa_discordnotify_installed_should_return_false(self):
        """
        Test should return False if discordnotify is not installed.
        """
        self.assertFalse(discordnotify_installed())

    @modify_settings(INSTALLED_APPS={"append": "discordnotify"})
    def test_aa_discordnotify_installed_should_return_true(self):
        """
        Test should return True if discordnotify is installed.
        """
        self.assertTrue(discordnotify_installed())
