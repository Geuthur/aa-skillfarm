# Standard Library
import socket

# Django
from django.test import RequestFactory, TestCase

# AA Skillfarm
from skillfarm.tests.testdata.integrations.allianceauth import load_allianceauth
from skillfarm.tests.testdata.integrations.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.utils import create_user_from_evecharacter


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
        # Initialize Alliance Auth test data
        load_allianceauth()
        load_eveuniverse()

        # Request Factory
        cls.factory = RequestFactory()

        # User with Standard Access
        cls.user, cls.user_character = create_user_from_evecharacter(
            character_id=1001,
            permissions=["skillfarm.basic_access"],
        )
        # User without Access to Skillfarm
        cls.no_permission_user, cls.no_perm_character = create_user_from_evecharacter(
            character_id=1002,
            permissions=[],
        )

        # User with Superuser Access
        cls.superuser, cls.superuser_character = create_user_from_evecharacter(
            character_id=1003,
            permissions=[],
        )
        cls.superuser.is_superuser = True
        cls.superuser.save()
