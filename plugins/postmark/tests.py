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
from .earwig import PostmarkContact
from ..utils import body_template_to_string, subject_template_to_string

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


class PostmarkMessageTest(BaseTests, TestCase):
    '''Tests sending a message using a mock pystmark library. Assumes the
    library does what it's supposed to and the message is successfully sent.
    '''
    plugin = PostmarkContact()
    def test_message(self):

        attempt = DeliveryAttempt.objects.get(pk=1)
        debug_info = self.plugin.send_message(attempt, debug=True)
        ctx = dict(
            attempt=attempt,
            login_url=getattr(settings, 'LOGIN_URL', 'PUT REAL LOGIN URL HERE'))

        path = 'plugins/default/email/body.html'
        body_html = plugin.render_template(path, **ctx)

        path = 'plugins/default/email/body.txt'
        body_txt = plugin.render_text_template(path, **ctx)

        path = 'plugins/default/email/subject.txt'
        subject = plugin.render_template(path, **ctx)

        self.assertEqual(debug_info['html'], body_html)
        self.assertEqual(debug_info['text'], body_txt)


class BounceHandlingTest(BaseTests, TestCase):
    '''Verify that a hypothetical bounce notifaction from postmark results
    in an accurate RecieverFeedback record.
    '''

    plugin = PostmarkContact()

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
        attempt = DeliveryAttempt.objects.get(pk=1)
        debug_info = self.plugin.send_message(attempt, debug=True)
        meta = debug_info['obj']

        # Make this id point at the bounced email.
        pystmark.BOUNCED_EMAIL_ID = str(meta.message_id)
