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
    # FIXME: test that email content is reasonable
    #def test_message(self):
    #    plugin = SESContact()
    #    attempt = DeliveryAttempt.objects.get(pk=1)
    #    debug_info = plugin.send_message(attempt, debug=True)
    #    self.assertEqual(debug_info['subject'], 'Test subject')
    #    self.assertEqual(debug_info['body'], 'Test body\n')

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
