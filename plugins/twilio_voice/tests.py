import os
import sys
import lxml.etree

# We're forcing this in before we import the
# models, that way we don't actually use the system copy.
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '../mock_libs'))

from django.test import TestCase, Client

from contact.models import (Sender, DeliveryAttempt, Message, Application, MessageRecipient,
                            FeedbackType)

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

        # 1 is messages root
        # 9 is call by error

        resp = self._twilio_call(
            '/plugins/twilio_voice/intro/%s/' % (attempt.id), Digits="1")
        redirect, = resp.xpath("//Redirect/text()")
        assert redirect.strip() == "../../messages/%s/" % (attempt.id)

        attempt = DeliveryAttempt.objects.get(id=attempt.id)
        assert attempt.feedback_type == FeedbackType.none

        resp = self._twilio_call(
            '/plugins/twilio_voice/intro/%s/' % (attempt.id), Digits="9")
        redirect, = resp.xpath("//Redirect/text()")
        assert redirect.strip() == "../../flag/%s/" % (attempt.id)

        # We don't flag until we follow the href.

        attempt = DeliveryAttempt.objects.get(id=attempt.id)
        assert attempt.feedback_type == FeedbackType.none

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

    def test_machine_intro(self):
        attempt = self.make_delivery_attempt('voice', '202-555-2222')
        self.plugin.send_message(attempt)
        resp = self._twilio_call(
            '/plugins/twilio_voice/intro/%s/' % (attempt.id),
            AnsweredBy="machine"
        )
        assert 'Hangup' in [x.tag for x in resp.xpath("./*")]

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

    def test_flagging(self):
        attempt = self.make_delivery_attempt('voice', '202-555-2222')
        self.plugin.send_message(attempt)

        attempt = DeliveryAttempt.objects.get(id=attempt.id)
        assert attempt.feedback_type == FeedbackType.none

        self._twilio_call(
            '/plugins/twilio_voice/flag/%s/' % (attempt.id)
        )

        attempt = DeliveryAttempt.objects.get(id=attempt.id)
        assert attempt.feedback_type == FeedbackType.wrong_person

    def test_two_message_views(self):
        attempt = self.make_delivery_attempt('voice', '202-555-2222')

        app = Application.objects.create(name="test2",
                                         contact="fnord@fnord.fnord",
                                         template_set="None", active=True)

        send = Sender.objects.create(
            id='randomstring2',
            email_expires_at=datetime(2020, 1, 1, tzinfo=utc)
        )

        message = Message.objects.create(
            type='fnord', sender=send, subject="Hello, World WORLD",
            message="HELLO WORLD WORLD", application=app
        )

        mr = MessageRecipient.objects.create(
            message=message, recipient=self.person,
            status='pending'
        )

        attempt.messages.add(mr)

        message = Message.objects.create(
            type='fnord', sender=send, subject="Hello, World WORLDS",
            message="HELLO WORLD WORLDS", application=app
        )

        mr = MessageRecipient.objects.create(
            message=message, recipient=self.person,
            status='pending'
        )

        attempt.messages.add(mr)
        self.plugin.send_message(attempt)

        messages = attempt.messages.order_by('id').all()
        message_counts = len(messages)

        for index, message in enumerate(messages):
            resp = self._twilio_call(
                '/plugins/twilio_voice/message/%s/%s/' % (attempt.id, index)
            )
            says = resp.xpath("//Say/text()")
            for say in says:
                if message.message.message in say:
                    break
            else:
                assert False, "I didn't find the right message in this view"

            resp = self._twilio_call(
                '/plugins/twilio_voice/message/%s/%s/' % (attempt.id, index),
                Digits="1",
            )

            says, = [x.strip() for x in resp.xpath("//Redirect/text()")]
            if (index + 1) < message_counts:
                assert says == "../../../message/%s/%s/" % (attempt.id,
                                                            (index + 1))
            else:
                assert says == "../../../intro/%s/" % (attempt.id)
