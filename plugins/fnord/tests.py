from django.test import TestCase
from ..base.tests import BaseTests
from .earwig import FnordContact


class FnordTests(BaseTests, TestCase):
    plugin = FnordContact()

    def test_message(self):
        plugin = FnordContact()
        debug_info = plugin.send_message(self.email_attempt, debug=True)
        self.assertIn(self.email_attempt.messages.all()[0].message.subject, debug_info['subject'])
        self.assertIn(self.email_attempt.messages.all()[0].message.message, debug_info['body'])
        self.assertIn(self.email_attempt.unsubscribe_url, debug_info['body'])
