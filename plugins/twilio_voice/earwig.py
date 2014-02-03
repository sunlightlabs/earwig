from __future__ import print_function
from django.conf import settings

from contact.errors import InvalidContactValue
from ..utils import body_template_to_string, subject_template_to_string
from .. import ContactPlugin
from .models import TwilioVoiceStatus

import twilio
from twilio.rest import TwilioRestClient


class TwilioVoiceContact(ContactPlugin):
    def __init__(self):
        twilio_settings = settings.CONTACT_PLUGIN_TWILIO
        self.settings = twilio_settings

        self.client = TwilioRestClient(
            self.settings['account_sid'],
            self.settings['auth_token'],
        )

    def send_message(self, attempt, debug=True):
        cd = attempt.contact
        from_number = self.settings['from_number']
        callback_url = "http://public.pault.ag/stuff/hello.xml"

        call = self.client.calls.create(to=cd.value,
                                        from_=from_number,
                                        url=callback_url)

    def check_message_status(self, attempt):
        obj = TwilioVoiceStatus.objects.get(attempt=attempt)
        return "sent" if obj.sent else "failed"
