"""TestView class."""

# Standard Library
from unittest.mock import Mock, patch

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth
from allianceauth.authentication.models import UserProfile

# AA Skillfarm
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import create_user_from_evecharacter_with_access
from skillfarm.views import add_info_to_context

MODULE_PATH = "skillfarm.views."


class TestAddInfoContext(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.factory = RequestFactory()
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )

    def test_add_info_context(self):
        request = self.factory.get(reverse("skillfarm:index"))
        request.user = self.user
        request.user.profile.theme = "dark"
        request.user.profile.save()
        context = {
            "page_title": "Skillfarm",
            "character_id": 1001,
        }
        response = add_info_to_context(request, context)

        new_context = {
            "theme": "dark",
            **context,
        }
        self.assertEqual(response, new_context)

    def test_add_info_context_no_userprofile(self):
        UserProfile.objects.filter(user=self.user).delete()
        request = self.factory.get(reverse("skillfarm:index"))
        request.user = self.user

        context = {
            "page_title": "Skillfarm",
            "character_id": 1001,
        }
        response = add_info_to_context(request, context)

        new_context = {
            "theme": None,
            **context,
        }
        self.assertEqual(response, new_context)
