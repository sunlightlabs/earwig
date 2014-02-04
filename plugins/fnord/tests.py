from django.test import TestCase
from ..base.tests import BaseTests
from .earwig import FnordContact


class FnordTests(BaseTests, TestCase):
    plugin = FnordContact()

    def test_status(self):
        """ Ensure that we can properly fetch the status out of the DB """
        plugin = FnordContact()
        plugin.send_message(self.attempt, debug=True)
        id1 = plugin.check_message_status(self.attempt)

        plugin = FnordContact()
        id2 = plugin.check_message_status(self.attempt)

        assert id1 == id2, ("We got a different result from a check when"
                            " given a new plugin object. DB issue?")

    def test_message(self):
        plugin = FnordContact()
        debug_info = plugin.send_message(self.attempt, debug=True)
        assert debug_info['subject'] == ''
        assert debug_info['body'] == """green blue red blue red green green


    HELLO WORLD

"""
