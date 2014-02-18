import os
import sys

# We're forcing this in before we import the
# models, that way we don't actually use the system copy.
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '../mock_libs'))

from django.test import TestCase, Client

from contact.models import (
    Person,
    ContactDetail,
    Sender,
    DeliveryAttempt,
    Message,
    Application,
    MessageRecipient,
)
from .earwig import TwilioVoiceContact
from django.conf import settings
from datetime import datetime
from django.utils.timezone import utc
from ..base.tests import BaseTests

settings.CONTACT_PLUGIN_TWILIO = {
    "account_sid": "ACTEST",
    "auth_token": "NONAME",
    "from_number": "test",
}


class TestTwilioVoice(BaseTests, TestCase):
    plugin = TwilioVoiceContact()

    def test_jacked_sid(self):
        c = Client()
        attempt = self.make_delivery_attempt('phone', '202-555-2222')
        self.plugin.send_message(attempt)
        resp = c.post('/plugins/twilio_voice/call/%s/' % (attempt.id), {
            "AccountSid": "ACFOOFOOFOOFOOFOOFOOFOOFOOFOO",
        })
        assert resp.status_code == 404

    def test_voice_sending(self):
        c = Client()
        attempt = self.make_delivery_attempt('phone', '202-555-2222')
        self.plugin.send_message(attempt)
        # Right, great.
        assert attempt.status == 'scheduled'

        resp = c.post('/plugins/twilio_voice/call/%s/' % (attempt.id), {
            "AccountSid": "ACTEST"
        })
        assert resp.status_code == 200

        dba = DeliveryAttempt.objects.get(id=attempt.id)
        assert dba.status == 'sent'

    def test_voice_response(self):
        c = Client()
        attempt = self.make_delivery_attempt('phone', '202-555-2222')
        self.plugin.send_message(attempt)
        resp = c.post('/plugins/twilio_voice/call/%s/' % (attempt.id), {
            "AccountSid": "ACTEST"
        })
        assert resp.content == b"<thing>HELLO, WORLD\n</thing>\n"
