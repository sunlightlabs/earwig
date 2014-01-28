import sys
import os

# We're forcing this in before we import the
# models, that way we don't actually use the system copy.
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '../mock_libs'))

from datetime import datetime
from django.test import TestCase
from django.db import IntegrityError
import pytz
import twilio
import twilio.rest

from contact.errors import InvalidContactValue
from contact.models import (
    Person,
    ContactDetail,
    Sender,
    DeliveryAttempt,
    Message,
    ContactPlugin,
)
from .earwig import TwilioContact


class TwilioTests(TestCase):

    def create_test_attempt(self):
        pt = Person.objects.create(ocd_id='test', title='Mr.', name='Paul Tagliamonte',
                                   photo_url="")
        cd = ContactDetail.objects.create(person=pt, type='sms', value='good', note='Twilio!',
                                          blacklisted=False)
        send = Sender.objects.create(email_expires_at=datetime.now(pytz.timezone('US/Eastern')))
        message = Message(type='fnord', sender=send, subject="Hello, World", message="HELLO WORLD")
        attempt = DeliveryAttempt(contact=cd, status="scheduled",
                                  plugin=self.plugin_model,
                                  date=datetime.now(pytz.timezone('US/Eastern')),
                                  engine="default")
        attempt.save()
        return attempt

    def setUp(self):
        self.plugin = TwilioContact()
        self.plugin_model = ContactPlugin(path='plugins.twilio.earwig',
                                          name='twilio',
                                          type='sms')
        self.plugin_model.save()

    def test_duplicate(self):
        """ Ensure that we blow up with two identical inserts """
        attempt = self.create_test_attempt()
        self.plugin.send_message(attempt)

        try:
            self.plugin.send_message(attempt)
            assert True is False, ("We didn't get an IntegrityError out of "
                                   "send_message")
        except IntegrityError:
            pass

    def test_status(self):
        """ Ensure that we can properly fetch the status out of the DB """
        plugin = TwilioContact()
        attempt = self.create_test_attempt()
        plugin.send_message(attempt)
        id1 = plugin.check_message_status(attempt)

        plugin = TwilioContact()
        id2 = plugin.check_message_status(attempt)

        assert id1 == id2, ("We got a different result from a check when"
                            " given a new plugin object. DB issue?")

    def test_bad_number(self):
        """ Ensure that we blow up with two identical inserts """
        attempt = self.create_test_attempt()
        attempt.contact.value = 'bad'
        attempt.contact.save()

        plugin = TwilioContact()
        self.assertRaises(InvalidContactValue, plugin.send_message, attempt)
