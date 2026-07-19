# Standard Library
import socket

# Django
from django.test import RequestFactory, TestCase

# AA Skillfarm
from skillfarm.tests.testdata.factory import EveCorporationInfoFactory, UserMainFactory
from skillfarm.tests.testdata.integrations.allianceauth import load_allianceauth


class SocketAccessError(Exception):
    """Error raised when a test script accesses the network"""


class NoSocketsTestCase(TestCase):
    """Variation of Django's TestCase class that prevents any network use.

    Example:

        .. code-block:: python

            class TestMyStuff(BaseTestCase):
                def test_should_do_what_i_need(self): ...

    """

    @classmethod
    def setUpClass(cls):
        cls.socket_original = socket.socket
        socket.socket = cls.guard
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        socket.socket = cls.socket_original
        return super().tearDownClass()

    @staticmethod
    def guard(*args, **kwargs):
        raise SocketAccessError("Attempted to access network")


class SkillFarmTestCase(NoSocketsTestCase):
    """
    Preloaded Testcase class for SkillFarm tests without Network access.

    Pre-Load:
        * Alliance Auth Characters, Corporation, Alliance Data
        * Eve Universe Data

    Available Request Factory:
        `self.factory`

    Available test users:
        * `user` User with standard Skillfarm access.
            * 'skillfarm.basic_access' Permission
            * Character ID 1001
        * `no_permission_user` User without any Skillfarm permissions.
            * No Permissions
            * Character ID 1002
        * `superuser` Superuser.
            * Access to whole Application
            * Character ID 1003

    Example:
        .. code-block:: python

            class TestMySkillFarmStuff(SkillFarmTestCase):
                def test_should_do_what_i_need(self):
                    user = self.user
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.corp = EveCorporationInfoFactory(
            corporation_id=98_000_000, corporation_name="Test Corporation"
        )
        # Initialize Alliance Auth test data
        load_allianceauth()

        # Request Factory
        cls.factory = RequestFactory()

        # User with Standard Access
        cls.user = UserMainFactory(main_character__corporation=cls.corp)
        cls.user_character = cls.user.profile.main_character

        # User with Superuser Access
        cls.superuser = UserMainFactory()
        cls.superuser.is_superuser = True
        cls.superuser.save()
        cls.superuser_character = cls.superuser.profile.main_character

        # User without Access to Skillfarm
        cls.no_permission_user = UserMainFactory(permissions__=[])
        cls.no_perm_character = cls.no_permission_user.profile.main_character
