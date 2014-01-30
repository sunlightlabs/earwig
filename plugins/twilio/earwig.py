from __future__ import print_function
from django.conf import settings

from contact.errors import InvalidContactValue
from ..utils import body_template_to_string, subject_template_to_string
from .. import ContactPlugin
from .models import TwilioStatus

import twilio
from twilio.rest import TwilioRestClient


class TwilioContact(ContactPlugin):
    def __init__(self):
        # XXX: How do we get these?
        twilio_settings = settings.CONTACT_PLUGIN_TWILIO
        self.settings = twilio_settings

        self.client = TwilioRestClient(
            self.settings['account_sid'],
            self.settings['auth_token'],
        )

    def send_message(self, attempt):
        # OK. let's ensure this is something we can handle.

        cd = attempt.contact

        from_number = self.settings['from_number']

        obj = TwilioStatus.objects.create(
            attempt=attempt,
            sent_to=cd.value,
            sent_from=from_number,
            sent=False
        )

        body = body_template_to_string(attempt.template, 'sms', attempt)
        subject = subject_template_to_string(attempt.template, 'sms', attempt)

        try:
            self.client.messages.create(to=cd.value,
                                        from_=from_number,
                                        subject=subject,
                                        body=body)
            obj.sent = True
        except twilio.TwilioRestException as e:
            print(e)
            raise InvalidContactValue("Contact detail value seems wrong")

        obj.save()

    def check_message_status(self, attempt):
        obj = TwilioStatus.objects.get(attempt=attempt)
        return "sent" if obj.sent else "failed"
