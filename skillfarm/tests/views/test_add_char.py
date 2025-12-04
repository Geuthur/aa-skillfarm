"""TestView class."""

# Standard Library
from http import HTTPStatus
from unittest.mock import Mock, patch

# Django
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponseRedirect
from django.test import override_settings
from django.urls import reverse

# AA Skillfarm
from skillfarm.models.skillfarmaudit import SkillFarmAudit
from skillfarm.tests import SkillFarmTestCase
from skillfarm.tests.testdata.utils import create_user_from_evecharacter
from skillfarm.views import add_char

MODULE_PATH = "skillfarm.views"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAddCharView(SkillFarmTestCase):
    """Test Add Character View."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _add_character(self, user, token) -> HttpResponseRedirect:
        """
        Helper to call add_char view.
        """
        request = self.factory.get(reverse("skillfarm:add_char"))
        request.user = user
        request.token = token
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        orig_view = add_char.__wrapped__.__wrapped__.__wrapped__
        return orig_view(request, token)

    def test_add_char(self, mock_tasks, mock_messages):
        """
        Test should
        * Add Skillfarm Character
        * Trigger update_character task
        * Show success message
        * Redirect to index
        """
        # given
        user = self.user
        token = user.token_set.get(character_id=1001)
        # when
        response = self._add_character(user, token)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("skillfarm:index"))
        self.assertTrue(mock_tasks.update_character.apply_async.called)
        self.assertTrue(mock_messages.success.called)
        self.assertTrue(
            SkillFarmAudit.objects.filter(character__character_id=1001).exists()
        )
