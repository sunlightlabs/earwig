import os
import sys
import lxml.etree

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

    def _twilio_call(self, url, **kwargs):
        c = Client()
        data = {"AccountSid": "ACTEST"}
        data.update(kwargs)
        resp = c.post(url, data)

        if resp.content.strip() == b"":
            raise ValueError("View returned empty response.")

        return lxml.etree.fromstring(resp.content)

    def test_jacked_sid(self):
        c = Client()
        attempt = self.make_delivery_attempt('voice', '202-555-2222')
        self.plugin.send_message(attempt)
        resp = c.post('/plugins/twilio_voice/intro/%s/' % (attempt.id), {
            "AccountSid": "ACFOOFOOFOOFOOFOOFOOFOOFOOFOO",
        })
        assert resp.status_code == 404

    def test_voice_sending(self):
        c = Client()
        attempt = self.make_delivery_attempt('voice', '202-555-2222')
        self.plugin.send_message(attempt)
        # Right, great.
        assert attempt.status == 'scheduled'

        resp = c.post('/plugins/twilio_voice/intro/%s/' % (attempt.id), {
            "AccountSid": "ACTEST"
        })
        assert resp.status_code == 200

        dba = DeliveryAttempt.objects.get(id=attempt.id)
        assert dba.status == 'sent'

    def test_intro(self):
        attempt = self.make_delivery_attempt('voice', '202-555-2222')
        self.plugin.send_message(attempt)
        resp = self._twilio_call(
            '/plugins/twilio_voice/intro/%s/' % (attempt.id)
        )
        message_count = len(attempt.messages.all())
        string = resp.xpath("//Say/text()")[0]

        assert str(message_count) in string
        assert "message" in string.lower()

    def test_messages(self):
        attempt = self.make_delivery_attempt('voice', '202-555-2222')
        self.plugin.send_message(attempt)
        resp = self._twilio_call(
            '/plugins/twilio_voice/messages/%s/' % (attempt.id)
        )
        redirects = resp.xpath("//Redirect/text()")
        for string in redirects:
            if "message/%s/%s/" % (attempt.id, 0) in string:
                break
        else:
            assert False, "Didn't find a redirect to the first message."

    def test_message(self):
        attempt = self.make_delivery_attempt('voice', '202-555-2222')
        self.plugin.send_message(attempt)
        resp = self._twilio_call(
            '/plugins/twilio_voice/message/%s/0/' % (attempt.id)
        )
        says = resp.xpath("//Say/text()")
        message, = attempt.messages.all()
        message = message.message.message  # wat.

        for say in says:
            if message in say:
                break
        else:
            assert False, "Didn't spot the message body in the endpoint"
