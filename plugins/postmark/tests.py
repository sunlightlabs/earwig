import os
import sys
from os.path import abspath, dirname, join

# We're forcing this in before we import the
# models, that way we don't actually use the system copy.
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '../mock_libs'))

import json
import uuid
import datetime as dt

from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from django.conf import settings

import pystmark

from plugins.postmark.models import PostmarkDeliveryMeta
from ..utils import body_template_to_string, subject_template_to_string
from .earwig import PostmarkContact

from contact.models import DeliveryAttempt
from contact.models import (
    Person,
    ContactDetail,
    Sender,
    Message,
    MessageRecipient,
    DeliveryAttempt,
    Application)
from contact.utils import utcnow


class EmailTestCase(TestCase):
    '''Base test case that switches the TEMPLATE_DIRS settings and
    adds test objects to the database.
    '''
    def setUp(self):
        self.create_attempt()
        self.switch_templatedirs()

    def switch_templatedirs(self):
        '''Swtich TEMPLATE_DIRS to point at test templates.
        '''
        self._templates = settings.TEMPLATE_DIRS
        dirs = [abspath(join(dirname(__file__), '..', 'test_templates'))]
        settings.TEMPLATE_DIRS = dirs

    def create_attempt(self):
        '''Create a test attempt to use in the tests.
        '''
        app = Application.objects.create(
            name="Testyapp", contact="example@example.com",
            template_set="cow")

        person = Person.objects.create(
            ocd_id='test', title='Mr.',
            name='Paul Tagliamonte', photo_url="")

        contact = ContactDetail.objects.create(
            person=person, type='email',
            value='paultag@sunlightfoundation.com', note='Holla at me', blacklisted=False)

        sender = Sender.objects.create(
            name="Testy McZample", id=uuid.uuid4(),
            email_expires_at=utcnow() + dt.timedelta(weeks=500))

        message = Message.objects.create(
            type='fnord', sender=sender, application=app,
            subject="Hello, World", message="HELLO WORLD")

        message_recipient = MessageRecipient(
            message=message,
            recipient=person,
            status='pending')
        message_recipient.save()

        attempt = DeliveryAttempt.objects.create(
            contact=contact, status="scheduled",
            engine="default",
            template='postmark-testing-deterministic-name')

        attempt.messages.add(message_recipient)

        attempt.save()
        return attempt

    def tearDown(self):
        '''Restore the template dirs and delete the test objects.
        '''
        settings.TEMPLATE_DIRS = self._templates
        Application.objects.all().delete()
        Person.objects.all().delete()
        ContactDetail.objects.all().delete()
        Sender.objects.all().delete()
        Message.objects.all().delete()
        MessageRecipient.objects.all().delete()
        DeliveryAttempt.objects.all().delete()


class PostmarkMessageTest(EmailTestCase):
    '''Tests sending a message using a mock pystmark library. Assumes the
    library does what it's supposed to and the message is successfully sent.
    '''
    def test_message(self):
        plugin = PostmarkContact()
        attempt = DeliveryAttempt.objects.get(pk=1)
        debug_info = plugin.send_message(attempt, debug=True)
        self.assertEqual(debug_info['subject'], 'Test subject')
        self.assertEqual(debug_info['body'], 'Test body\n')


class ContactDetailTest(EmailTestCase):

    def test_blacklist(self):
        '''Verify the plugin raises an error if it the contact
        detail is blacklisted.
        '''
        email = "paultag@sunlightfoundation.com"
        paul = ContactDetail.objects.get(value=email)
        paul.blacklisted = True
        paul.save()
        plugin = PostmarkContact()
        attempt = DeliveryAttempt.objects.get(pk=1)
        with self.assertRaises(ValueError):
            plugin.send_message(attempt, debug=True)

    def test_wrong_medium(self):
        '''Verify that the email plugin balks if told to send an sms.
        '''
        email = "paultag@sunlightfoundation.com"
        paul = ContactDetail.objects.get(value=email)
        paul.type = 'sms'
        paul.save()
        plugin = PostmarkContact()
        attempt = DeliveryAttempt.objects.get(pk=1)
        with self.assertRaises(ValueError):
            plugin.send_message(attempt, debug=True)


class BounceHandlingTest(EmailTestCase):
    '''Verify that a hypothetical bounce notifaction from postmark results
    in an accurate RecieverFeedback record.
    '''

    def test_hard_bounce(self):
        '''Verify that hard bounces result in DeliveryAttempt.status
        being toggled to 'bad-data'.
        '''
        attempt = DeliveryAttempt.objects.get(pk=1)

        # Assume an email message has been sent.
        PostmarkDeliveryMeta.objects.create(attempt=attempt, message_id='test-hard-bounce')

        # Simulate a bounce notification from postmark.
        client = Client()
        payload = {
            "ID": [],
            "Type": "HardBounce",
            "Tag": "Invitation",
            "MessageID": "test-hard-bounce",
            "TypeCode": 1,
            "Email": "jim@test.com",
            "BouncedAt": "2010-04-01",
            "Details": "test bounce",
            "DumpAvailable": True,
            "Inactive": True,
            "CanActivate": True,
            "Subject": "Hello from our app!"
        }
        client.post(reverse('handle_bounce'), json.dumps(payload),
                    content_type='application/json')

        attempt = DeliveryAttempt.objects.get(pk=1)

        # Make sure the hard bounce was recorded as vendor-hard-bounce.
        self.assertEqual(attempt.status, 'bad-data')

    def test_blocked(self):
        '''Verify that "blocked" notifcations from postmark result in
        a RecieverFeedback instance with feedback_type = 'vendor-blocked'.
        '''
        attempt = DeliveryAttempt.objects.all()[0]

        # Assume an email message has been sent.
        PostmarkDeliveryMeta.objects.create(attempt=attempt, message_id='test-blocked')

        # Simulate a bounce notification from postmark.
        client = Client()
        payload = {
            "ID": [],
            "Type": "Blocked",
            "Tag": "Invitation",
            "MessageID": "test-blocked",
            "TypeCode": 1,
            "Email": "jim@test.com",
            "BouncedAt": "2010-04-01",
            "Details": "test bounce",
            "DumpAvailable": True,
            "Inactive": True,
            "CanActivate": True,
            "Subject": "Hello from our app!"
        }
        client.post(reverse('handle_bounce'), json.dumps(payload), content_type='application/json')
        attempt = DeliveryAttempt.objects.all()[0]

        # Make sure the hard bounce was recorded as vendor-hard-bounce.
        self.assertEqual(attempt.status, 'blocked')

    def test_bounce_status(self):
        plugin = PostmarkContact()
        attempt = DeliveryAttempt.objects.get(pk=1)
        debug_info = plugin.send_message(attempt, debug=True)
        meta = debug_info['obj']

        # Make this id point at the bounced email.
        pystmark.BOUNCED_EMAIL_ID = str(meta.message_id)
        status = plugin.check_message_status(attempt)
        self.assertEqual(status, 'bad-data')
