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


class TestTwilioVoice(TestCase):

    def test_voice_sending(self):
        c = Client()
        #resp = c.post('/sender/', {
        #    'email': 'test@example.com',
        #    'name': 'Test',
        #    'ttl': 7
        #})

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
        self.plugin = TwilioVoiceContact()

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
