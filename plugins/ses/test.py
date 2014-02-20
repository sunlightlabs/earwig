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


class SESMessageTest(BaseTests, TestCase):
    '''Tests sending a message using a mock pystmark library. Assumes the
    library does what it's supposed to and the message is successfully sent.
    '''
    plugin = SESContact()
    def test_message(self):

        attempt = DeliveryAttempt.objects.get(pk=1)
        debug_info = self.plugin.send_message(attempt, debug=True)
        login_url = getattr(settings, 'LOGIN_URL', 'PUT REAL LOGIN URL HERE')
        ctx = dict(attempt=attempt, login_url=login_url)

        path = 'plugins/default/email/body.txt'
        body_txt = self.plugin.render_template(path, **ctx)

        path = 'plugins/default/email/subject.txt'
        subject = self.plugin.render_template(path, **ctx)

        # Assert that templates got rendered to the expected output.
        self.assertEqual(debug_info['text'], body_txt)

        # --------------------------------------------------------------------
        # Now several sanity checks to make sure the model content
        # is ending up the rendered output:
        # --------------------------------------------------------------------

        # 1) Make sure the first 300 characters of each message
        #    are being displayed.
        for message in attempt.messages.values_list('message__message', flat=True):
            self.assertIn(message[:300], body_txt)

        # 2) Make sure the recipient's full name is displayed.
        self.assertIn(attempt.contact.person.name, body_txt)

        # 3) Make sure each sender's name is displayed.
        for name in attempt.messages.values_list('message__sender__name', flat=True):
            self.assertIn(name, body_txt)

        # 4) Verify that the unsubscribe url is displayed.
        self.assertIn(attempt.unsubscribe_url, body_txt)

        # 5) Verify that login url is displayed.
        self.assertIn(login_url, body_txt)


class BounceHandlingTest(BaseTests, TestCase):
    '''Verify that a hypothetical bounce notifaction from postmark results
    in an accurate RecieverFeedback record.
    '''
    plugin = SESContact()

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
