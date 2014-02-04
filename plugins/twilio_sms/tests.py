import sys
import os

# We're forcing this in before we import the
# models, that way we don't actually use the system copy.
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '../mock_libs'))

from datetime import datetime
from django.test import TestCase
from django.db import IntegrityError
from django.utils.timezone import utc
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
    Application,
    MessageRecipient,
)
from .earwig import TwilioSMSContact
from django.conf import settings


class TwilioSMSTests(TestCase):

    def create_test_attempt(self):
        app = Application.objects.create(name="test", contact="fnord@fnord.fnord",
            template_set="None", active=True)

        pt = Person.objects.create(
            ocd_id='test', title='Mr.', name='Paul Tagliamonte', photo_url="")

        cd = ContactDetail.objects.create(
            person=pt, type='sms', value='good', note='Twilio!',
            blacklisted=False)

        send = Sender.objects.create(
            id='randomstring', email_expires_at=datetime(2020, 1, 1, tzinfo=utc))

        message = Message(
            type='fnord', sender=send, subject="Hello, World",
            message="HELLO WORLD", application=app)

        message.save()

        mr = MessageRecipient(message=message, recipient=pt, status='pending')
        mr.save()

        attempt = DeliveryAttempt(
            contact=cd, status="scheduled",
            template='twilio-testing-deterministic-name',
            engine="default")

        attempt.save()
        attempt.messages.add(mr)
        return attempt

    def setUp(self):
        self.plugin = TwilioSMSContact()

        # beyond this, we also need to mangle the path pretty bad.
        # so that we have our test templates set and nothing else. We'll
        # fix this after for the other tests.
        self._templates = settings.TEMPLATE_DIRS
        settings.TEMPLATE_DIRS = (
            os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         '..', 'test_templates')),
        )

    def tearDown(self):
        settings.TEMPLATE_DIRS = self._templates

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
        plugin = TwilioSMSContact()
        attempt = self.create_test_attempt()
        plugin.send_message(attempt)
        id1 = plugin.check_message_status(attempt)

        plugin = TwilioSMSContact()
        id2 = plugin.check_message_status(attempt)

        assert id1 == id2, ("We got a different result from a check when"
                            " given a new plugin object. DB issue?")

    def test_bad_number(self):
        """ Ensure that we blow up with two identical inserts """
        attempt = self.create_test_attempt()
        attempt.contact.value = 'bad'
        attempt.contact.save()

        plugin = TwilioSMSContact()
        self.assertRaises(InvalidContactValue, plugin.send_message, attempt)

    def test_message(self):
        plugin = TwilioSMSContact()
        attempt = self.create_test_attempt()
        debug_info = plugin.send_message(attempt, debug=True)
        assert debug_info['subject'] == ''
        assert debug_info['body'] == ("green blue red blue red green green. "
                                      "You've got 1 message(s).\n")
