import os
import sys
from os.path import abspath, dirname, join

# We're forcing this in before we import the
# models, that way we don't actually use the system copy.
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '../mock_libs'))

import time
import json
import uuid
import email
import datetime as dt

from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.timezone import utc

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
        login_url = getattr(settings, 'LOGIN_URL', 'PUT REAL LOGIN URL HERE')
        ctx = dict(attempt=attempt, login_url=login_url)

        path = 'plugins/default/email/body.html'
        body_html = self.plugin.render_template(path, **ctx)

        path = 'plugins/default/email/body.txt'
        body_txt = self.plugin.render_template(path, **ctx)

        path = 'plugins/default/email/subject.txt'
        subject = self.plugin.render_template(path, **ctx)

        # Assert that templates got rendered to the expected output.
        self.assertEqual(debug_info['html'], body_html)
        self.assertEqual(debug_info['text'], body_txt)

        # --------------------------------------------------------------------
        # Now several sanity checks to make sure the model content
        # is ending up the rendered output:
        # --------------------------------------------------------------------

        # 1) Make sure the first 300 characters of each message
        #    are being displayed.
        for message in attempt.messages.values_list('message__message', flat=True):
            self.assertIn(message[:300], body_html)
            self.assertIn(message[:300], body_txt)

        # 2) Make sure the recipient's full name is displayed.
        self.assertIn(attempt.contact.person.name, body_html)
        self.assertIn(attempt.contact.person.name, body_txt)

        # 3) Make sure each sender's name is displayed.
        for name in attempt.messages.values_list('message__sender__name', flat=True):
            self.assertIn(name, body_html)
            self.assertIn(name, body_txt)

        # 4) Verify that the unsubscribe url is displayed.
        self.assertIn(attempt.unsubscribe_url, body_html)
        self.assertIn(attempt.unsubscribe_url, body_txt)

        # 5) Verify that login url is displayed.
        self.assertIn(login_url, body_html)
        self.assertIn(login_url, body_txt)


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
        client.post(reverse('postmark.handle_bounce'), json.dumps(payload),
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
        client.post(reverse('postmark.handle_bounce'), json.dumps(payload), content_type='application/json')
        attempt = DeliveryAttempt.objects.all()[0]

        # Make sure the hard bounce was recorded as vendor-hard-bounce.
        self.assertEqual(attempt.status, 'blocked')

    def test_bounce_status(self):
        attempt = DeliveryAttempt.objects.get(pk=1)
        debug_info = self.plugin.send_message(attempt, debug=True)
        meta = debug_info['obj']

        # Make this id point at the bounced email.
        pystmark.BOUNCED_EMAIL_ID = str(meta.message_id)



class InboundTest(BaseTests, TestCase):
    '''Verify that inbound email (that has a MailboxHash) results
    in a reply object.
    '''
    plugin = PostmarkContact()

    def test_hard_bounce(self):
        '''Verify that hard bounces result in DeliveryAttempt.status
        being toggled to 'bad-data'.
        '''
        attempt = DeliveryAttempt.objects.get(pk=1)
        message_recip = attempt.messages.get()

        # Assume an email message has been sent.
        PostmarkDeliveryMeta.objects.create(attempt=attempt, message_id='test-hard-bounce')

        # Simulate a bounce notification from postmark.
        client = Client()
        payload = {
            "From": attempt.contact.value,
            "FromFull": {
                "Email": attempt.contact.value,
                "Name": "John Doe"
                },
            "To": "InboundHash+MailboxHash@inbound.postmarkapp.com",
            "ToFull": [{
                "Email": "InboundHash+MailboxHash@inbound.postmarkapp.com",
                "Name": ""
                }],
            "ReplyTo": self.plugin.get_reply_to(message_recip),
            "Subject": "This is an inbound message",
            "MessageID": "22c74902-a0c1-4511-804f2-341342852c90",
            "Date": "Thu, 5 Apr 2012 16:59:01 +0200",
            "MailboxHash": str(message_recip.id),
            "TextBody": "[ASCII]",
            "HtmlBody": "[HTML(encoded)]",
            "Tag": "",
            "Headers": [{
                "Name": "X-Spam-Checker-Version",
                "Value": "SpamAssassin 3.3.1 (2010-03-16) onrs-ord-pm-inbound1.wildbit.com"
                }]
            }
        client.post(
            reverse('postmark.handle_inbound'),
            json.dumps(payload),
            content_type='application/json')

        reply = attempt.messages.get().replies.get()
        created_at = email.utils.parsedate(payload['Date'])
        created_at = dt.datetime.fromtimestamp(time.mktime(created_at))
        created_at = created_at.replace(tzinfo=utc)

        self.assertEqual(reply.message_id, int(payload['MailboxHash']))
        self.assertEqual(reply.email, payload['FromFull']['Email'])
        self.assertEqual(reply.subject, payload['Subject'])
        self.assertEqual(reply.body, payload['TextBody'])
        self.assertEqual(reply.created_at, created_at)
