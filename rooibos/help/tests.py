from django.test import TestCase
from .templatetags import help


class HelpTestCase(TestCase):

    def test_append_context(self):
        self.assertEqual(
            'http://example.com/help',
            help.help_url_with_context('context', 'http://example.com/help'))
        self.assertEqual(
            'http://example.com/help?context',
            help.help_url_with_context('context', 'http://example.com/help?'))
        self.assertEqual(
            'http://example.com/help/context',
            help.help_url_with_context('context', 'http://example.com/help/'))
