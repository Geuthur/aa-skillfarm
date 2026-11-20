"""Tests for the EVE image helpers."""

# Standard Library
from unittest.mock import patch

# Django
from django.test import TestCase

# AA Skillfarm
from skillfarm.helpers import eveonline

MODULE_PATH = "skillfarm.helpers.eveonline."


class TestEveonlineHelpers(TestCase):
    def test_should_return_url(self):
        url = eveonline.get_character_portrait_url(1001, size=64)
        self.assertIn("/characters/1001/portrait", url)
        self.assertIn("size=64", url)

    def test_should_return_empty_string_for_invalid_id(self):
        with patch(MODULE_PATH + "character_portrait_url", side_effect=ValueError):
            self.assertEqual(eveonline.get_character_portrait_url(1001), "")

    def test_should_return_html_with_and_without_name(self):
        html = eveonline.get_character_portrait_url(
            1001, character_name="Bruce", as_html=True
        )
        self.assertIn('alt="Bruce"', html)
        self.assertNotIn("<span>", html)
        html = eveonline.get_character_portrait_url(
            1001, character_name="Bruce", as_html=True, display_name=True
        )
        self.assertIn("<span>Bruce</span>", html)

    def test_should_return_urls_and_html_for_other_entities(self):
        cases = (
            (eveonline.get_corporation_logo_url, "/corporations/2002/logo"),
            (eveonline.get_alliance_logo_url, "/alliances/3003/logo"),
            (eveonline.get_type_render_url, "/types/4004/render"),
            (eveonline.get_icon_render_url, "/types/4004/icon"),
        )
        for func, expected in cases:
            entity_id = int(expected.split("/")[2])
            with self.subTest(func=func.__name__):
                self.assertIn(expected, func(entity_id))
                html = func(entity_id, as_html=True)
                self.assertIn("<img", html)
                self.assertNotIn("<span>", html)
                html = func(entity_id, as_html=True, display_name=True)
                self.assertIn("<span>", html)
