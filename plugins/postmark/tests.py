import os
import sys

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
from django.template.loader import render_to_string

import mock
import pystmark

from plugins.postmark.models import PostmarkDeliveryMeta
from .earwig import PostmarkPlugin

from contact.models import DeliveryAttempt, DeliveryStatus
from ..base.tests import BaseTests


class PostmarkMessageTest(BaseTests, TestCase):
    '''Tests sending a message using a mock pystmark library. Assumes the
    library does what it's supposed to and the message is successfully sent.
    '''
    plugin = PostmarkPlugin()

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

    plugin = PostmarkPlugin()

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
    plugin = PostmarkPlugin()

    @mock.patch('pystmark.send')
    def test_message_reply(self, pystmark_send):
        '''Verify that inbound replies result in the creation of
        the correct MessageReply record.
        '''
        attempt = DeliveryAttempt.objects.get(pk=1)
        message_recip = attempt.messages.get()

        # Assume an email message has been sent.
        PostmarkDeliveryMeta.objects.create(attempt=attempt, message_id='test-hard-bounce')

        # Simulate in inbound email from postmark.
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

        self.assertEqual(reply.message_recip_id, int(payload['MailboxHash']))
        self.assertEqual(reply.subject, payload['Subject'])
        self.assertEqual(reply.body, payload['TextBody'])
        self.assertEqual(reply.created_at, created_at)

    @mock.patch('pystmark.send')
    def test_unsolicited(self, pystmark_send):
        '''Verify that unsolicited inbound emails result in a default
        email directing people to the site.
        '''
        # Simulate in inbound email from postmark.
        client = Client()
        payload = {
            "From": 'cow@example.com',
            "FromFull": {
                "Email": 'cow@example.com',
                "Name": "John Doe"
                },
            "To": "InboundHash+MailboxHash@inbound.postmarkapp.com",
            "ToFull": [{
                "Email": "InboundHash+MailboxHash@inbound.postmarkapp.com",
                "Name": ""
                }],
            "ReplyTo": 'cow@example.com',
            "Subject": "This is an inbound message",
            "MessageID": "22c74902-a0c1-4511-804f2-341342852c90",
            "Date": "Thu, 5 Apr 2012 16:59:01 +0200",
            "MailboxHash": None,
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

        # ---------------------------------------------------------------------
        # Create the message we expect to be sent.
        # ---------------------------------------------------------------------

        # Create the reply-to address.
        if settings.POSTMARK_MX_FORWARDING_ENABLED:
            inbound_host = settings.EARWIG_INBOUND_EMAIL_HOST
        else:
            inbound_host = settings.POSTMARK_INBOUND_HOST
        reply_to_tmpl = '{0.POSTMARK_INBOUND_HASH}@{1}'
        reply_to = reply_to_tmpl.format(settings, inbound_host)

        subject_tmpl = 'plugins/default/email/unsolicited/subject.txt'
        body_text_tmpl = 'plugins/default/email/unsolicited/body.txt'
        body_html_tmpl = 'plugins/default/email/unsolicited/body.html'

        message = pystmark.Message(
            sender=settings.EARWIG_EMAIL_SENDER,
            reply_to=reply_to,
            to=payload['FromFull']['Email'],
            subject=render_to_string(subject_tmpl, {}),
            text=render_to_string(body_text_tmpl, {}),
            html=render_to_string(body_html_tmpl, {}))

        # Verify it was called.
        pystmark_send.assert_called_once_with(
            message, settings.POSTMARK_API_KEY)


class ReplyForwardingTest(BaseTests, TestCase):

    plugin = PostmarkPlugin()

    @mock.patch('pystmark.send')
    def test_reply_forwarded_to_orig_sender(self, pystmark_send):
        '''If the target of an attempt replies, verify the reply gets
        forwarded to the original sender.
        '''
        attempt = DeliveryAttempt.objects.get(pk=1)
        message_recip = attempt.messages.get()

        # Assume an email message has been sent.
        PostmarkDeliveryMeta.objects.create(
            attempt=attempt, message_id='test-hard-bounce')

        # Simulate in inbound email from postmark.
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

        message_reply = attempt.messages.get().replies.get()
        to = message_reply.message_recip.message.sender.email
        reply_to = self.plugin.get_reply_to(message_reply.message_recip)
        ctx = dict(
            message_reply=message_reply,
            login_url=getattr(settings, 'LOGIN_URL', 'PUT REAL LOGIN URL HERE'))

        path = 'plugins/default/email/forwarded_reply/body.html'
        body_html = self.plugin.render_template(path, **ctx)
        path = 'plugins/default/email/forwarded_reply/body.txt'
        body_txt = self.plugin.render_template(path, **ctx)
        path = 'plugins/default/email/forwarded_reply/subject.txt'
        subject = self.plugin.render_template(path, **ctx)

        message = pystmark.Message(
            sender=settings.EARWIG_EMAIL_SENDER,
            reply_to=reply_to,
            to=to,
            subject=subject,
            text=body_txt,
            html=body_html)

        # Verify it was called.
        pystmark_send.assert_called_once_with(message, settings.POSTMARK_API_KEY)

    @mock.patch('pystmark.send')
    def test_reply_forwarded_to_legislator(self, pystmark_send):
        '''If the target of an attempt replies, verify the reply gets
        forwarded to the original sender.
        '''
        # Assume the attempt was succesfully delivered.
        attempt = DeliveryAttempt.objects.get(pk=1)
        attempt.mark_attempted(DeliveryStatus.success, self.plugin, 'cow')

        message_recip = attempt.messages.get()

        # Simulate in inbound email from the legislator.
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

        # Now simulate in inbound email (reply to legislator) from the user.
        client = Client()
        payload = {
            "From": 'oldschool@mario.com',
            "FromFull": {
                "Email": 'oldschool@mario.com',
                "Name": "Oldschool Mario"
                },
            "To": "InboundHash+%s@inbound.postmarkapp.com" % str(message_recip.id),
            "ToFull": [{
                "Email": "InboundHash+%s@inbound.postmarkapp.com" % str(message_recip.id),
                "Name": ""
                }],
            "ReplyTo": self.plugin.get_reply_to(message_recip),
            "Subject": "This is an inbound message",
            "MessageID": "22c74902-a0c1-4511-804f2-341342852c90",
            "Date": "Thu, 6 Apr 2012 16:59:01 +0200",
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

        # Ok, now there should be two reply objects. We want the most recent.
        replies = attempt.messages.get().replies.order_by('created_at')
        message_reply = list(replies)[-1]

        # The alert email goes to the recipient of the reply.
        to = message_reply.recipient_email()
        reply_to = self.plugin.get_reply_to(message_reply.message_recip)
        ctx = dict(
            message_reply=message_reply,
            login_url=getattr(settings, 'LOGIN_URL', 'PUT REAL LOGIN URL HERE'))

        path = 'plugins/default/email/forwarded_reply/body.html'
        body_html = self.plugin.render_template(path, **ctx)
        path = 'plugins/default/email/forwarded_reply/body.txt'
        body_txt = self.plugin.render_template(path, **ctx)
        path = 'plugins/default/email/forwarded_reply/subject.txt'
        subject = self.plugin.render_template(path, **ctx)

        message = pystmark.Message(
            sender=settings.EARWIG_EMAIL_SENDER,
            reply_to=reply_to,
            to=to,
            subject=subject,
            text=body_txt,
            html=body_html)

        # Verify it was called.
        pystmark_send.assert_called_with(message, settings.POSTMARK_API_KEY)
