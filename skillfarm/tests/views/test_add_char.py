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
from skillfarm.tests import AuthTestCase
from skillfarm.tests.testdata.skillfarm import UserMainFactory
from skillfarm.views import add_char

MODULE_PATH = "skillfarm.views"
LOGIN_PATH = "/account/login/"


@patch(MODULE_PATH + ".messages")
@patch(MODULE_PATH + ".tasks")
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestAddCharView(AuthTestCase):
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
        token = self.user.token_set.get(
            character_id=self.user.profile.main_character.character_id
        )
        # when
        response = self._add_character(self.user, token)
        # then
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("skillfarm:react_base"))
        self.assertTrue(mock_tasks.update_character.apply_async.called)
        self.assertTrue(mock_messages.success.called)
        self.assertTrue(
            SkillFarmAudit.objects.filter(
                character__character_id=self.user.profile.main_character.character_id
            ).exists()
        )


class TestAddCharViewPermission(AuthTestCase):
    """`add_char` checks `basic_access` before it starts the SSO flow."""

    def test_add_char_should_not_start_sso_without_basic_access(self):
        # Test Data
        user = UserMainFactory(permissions__=["skillfarm.admin_access"])
        self.client.force_login(user)

        # Test Action
        response = self.client.get(reverse("skillfarm:add_char"))

        # Expected Result: sent to the login page, no token selection and no SSO
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertIn(LOGIN_PATH, response["Location"])
        self.assertFalse(SkillFarmAudit.objects.exists())

    def test_add_char_should_start_sso_with_basic_access(self):
        # Test Data
        self.client.force_login(self.user)

        # Test Action
        response = self.client.get(reverse("skillfarm:add_char"))

        # Expected Result: token selection (200) or redirect to the SSO, not the login page
        self.assertIn(response.status_code, (HTTPStatus.OK, HTTPStatus.FOUND))
        self.assertNotIn(LOGIN_PATH, response.get("Location", ""))
