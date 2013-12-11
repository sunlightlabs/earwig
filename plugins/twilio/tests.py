import sys
import os

sys.path.insert(0, os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '../mock_libs'))  # We're forcing this in before we import the
# models, that way we don't actually use the system copy.

import twilio
import twilio.rest

import unittest
from django.test import TestCase
import datetime as dt
import pytz

from contact.errors import InvalidContactValue

from contact.models import (
    Person,
    ContactDetail,
    Sender,
    DeliveryAttempt,
    Message,
    MessageRecipient,
    DeliveryAttempt,
)

from .earwig import TwilioContact
from .models import TwilioStatus

from django.db import IntegrityError


def create_test_attempt():
    pt = Person.objects.create(ocd_id='test', title='Mr.',
                          name='Paul Tagliamonte', photo_url="")
    cd = ContactDetail.objects.create(person=pt, type='sms',
            value='', note='Twilio!', blacklisted=False)
    send = Sender.objects.create(email_expires_at=dt.datetime.now(pytz.timezone('US/Eastern')))
    message = Message(type='fnord', sender=send,
                      subject="Hello, World", message="HELLO WORLD")
    attempt = DeliveryAttempt(contact=cd, status="scheduled",
                              date=dt.datetime.now(pytz.timezone('US/Eastern')),
                              engine="default")
    attempt.save()
    return attempt


class TwilioTests(TestCase):
    def setUp(self):
        self.plugin = TwilioContact()

    def test_duplicate(self):
        """ Ensure that we blow up with two identical inserts """
        attempt = create_test_attempt()
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
        attempt = create_test_attempt()
        plugin.send_message(attempt)
        id1 = plugin.check_message_status(attempt)

        plugin = TwilioContact()
        id2 = plugin.check_message_status(attempt)

        assert id1 == id2, ("We got a different result from a check when"
                            " given a new plugin object. DB issue?")

    def test_bad_number(self):
        """ Ensure that we blow up with two identical inserts """
        attempt = create_test_attempt()
        attempt.contact.value = 'bad'
        attempt.contact.save()

        plugin = TwilioContact()
        self.assertRaises(InvalidContactValue, plugin.send_message, attempt)
