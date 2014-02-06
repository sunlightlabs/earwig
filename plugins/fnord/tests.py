from django.test import TestCase
from ..base.tests import BaseTests
from .earwig import FnordContact


class FnordTests(BaseTests, TestCase):
    plugin = FnordContact()

    def test_message(self):
        plugin = FnordContact()
        debug_info = plugin.send_message(self.attempt, debug=True)
        assert debug_info['subject'] == ''
        assert debug_info['body'] == """green blue red blue red green green


    HELLO WORLD

"""
