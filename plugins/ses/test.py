import os
import sys
from os.path import abspath, dirname, join

# We're forcing this in before we import the
# models, that way we don't actually use the system copy.
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '../mock_libs'))

import uuid
import datetime as dt

from django.test import TestCase
from django.conf import settings

from plugins.ses.models import SESDeliveryMeta
from ..utils import body_template_to_string, subject_template_to_string
from .earwig import SESContact

from contact.models import (
    Person,
    ContactDetail,
    Sender,
    Message,
    MessageRecipient,
    DeliveryAttempt,
    Application)
from contact.utils import utcnow
from ..base.tests import BaseTests


class EmailTestCase(TestCase):
    '''Base test case that switches the TEMPLATE_DIRS settings and
    adds test objects to the database.
    '''
    def setUp(self):
        self.create_attempt()

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
            engine="default")

        attempt.messages.add(message_recipient)

        attempt.save()
        return attempt

    def tearDown(self):
        '''Restore the template dirs and delete the test objects.
        '''
        Application.objects.all().delete()
        Person.objects.all().delete()
        ContactDetail.objects.all().delete()
        Sender.objects.all().delete()
        Message.objects.all().delete()
        MessageRecipient.objects.all().delete()
        DeliveryAttempt.objects.all().delete()


class SESMessageTest(EmailTestCase):
    '''Tests sending a message using a mock pystmark library. Assumes the
    library does what it's supposed to and the message is successfully sent.
    '''
    def test_message(self):
        plugin = SESContact()
        attempt = DeliveryAttempt.objects.get(pk=1)
        debug_info = plugin.send_message(attempt, debug=True)

        ctx = dict(
            attempt=attempt,
            login_url=getattr(settings, 'LOGIN_URL', 'PUT REAL LOGIN URL HERE'))

        path = 'plugins/default/email/body.html'
        body_html = plugin.render_template(path, **ctx)

        path = 'plugins/default/email/body.txt'
        body_txt = plugin.render_template(path, **ctx)

        path = 'plugins/default/email/subject.txt'
        subject = plugin.render_template(path, **ctx)

        # self.assertEqual(debug_info['html'], body_html)
        self.assertEqual(debug_info['text'], body_txt)


class ContactDetailTest(EmailTestCase):

    def test_blacklist(self):
        '''Verify the plugin raises an error if it the contact
        detail is blacklisted.
        '''
        email = "paultag@sunlightfoundation.com"
        paul = ContactDetail.objects.get(value=email)
        paul.blacklisted = True
        paul.save()
        plugin = SESContact()
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
        plugin = SESContact()
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

    def test_blocked(self):
        '''Verify that "blocked" notifcations from postmark result in
        a RecieverFeedback instance with feedback_type = 'vendor-blocked'.
        '''

    def test_bounce_status(self):
        pass
