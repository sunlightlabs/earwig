import sys
import os

# We're forcing this in before we import the
# models, that way we don't actually use the system copy.
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '../mock_libs'))

from datetime import datetime
from django.test import TestCase, Client
from django.db import IntegrityError
from django.utils.timezone import utc
import pytz
import twilio
import twilio.rest

from contact.models import (
    Person,
    ContactDetail,
    Sender,
    DeliveryAttempt,
    Message,
    Application,
    MessageRecipient,
    FeedbackType,
)
from .earwig import TwilioSmsContact
from django.conf import settings
from ..base.tests import BaseTests

settings.CONTACT_PLUGIN_TWILIO = {
    "account_sid": "ACTEST",
    "auth_token": "NONAME",
    "from_number": "test",
}


class TwilioSMSTests(BaseTests, TestCase):
    plugin = TwilioSmsContact()

    def test_unsubscribe(self):
        attempt = self.make_delivery_attempt('sms', '202-555-2222')
        self.plugin.send_message(attempt)
        c = Client()
        resp = c.post("/plugins/twilio_sms/text/", {
            "AccountSid": "ACTEST",
            "From": attempt.contact.value,
            "Body": "unsubscribe",
        })
        assert resp.status_code == 200, "Bad unsubscribe response - %s" % (
            resp.content
        )
        attempt = DeliveryAttempt.objects.get(id=attempt.id)
        assert attempt.feedback_type == FeedbackType.contact_detail_blacklist

    def test_bad_number(self):
        """ Ensure that we blow up with two identical inserts """
        attempt = self.make_delivery_attempt('sms', 'bad')

        plugin = TwilioSmsContact()
        plugin.send_message(attempt)
        assert attempt.status == 'bad_data'

    def test_message(self):
        plugin = TwilioSmsContact()
        attempt = self.make_delivery_attempt('sms', '202-555-1111')
        debug_info = plugin.send_message(attempt, debug=True)
        assert debug_info['subject'] == ''
        assert debug_info['body'] == ("green blue red blue red green green. "
                                      "You've got 1 message(s).\n")
