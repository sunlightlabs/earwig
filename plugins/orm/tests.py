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

from .earwig import OrmPlugin

from contact.models import DeliveryAttempt
from ..base.tests import BaseTests


class OrmMessageTest(BaseTests, TestCase):
    '''Tests sending a message using a mock pystmark library. Assumes the
    library does what it's supposed to and the message is successfully sent.
    '''
    plugin = OrmPlugin()

    def test_message(self):

        attempt = DeliveryAttempt.objects.get(pk=1)
        debug_info = self.plugin.send_message(attempt, debug=True)

        # Assert that templates got rendered to the expected output.
        msg = attempt.messages.get().message.message
        self.assertEqual(debug_info['msg'], msg)
