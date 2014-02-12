from __future__ import print_function
from django.conf import settings

from .models import TwilioSMSStatus
from ..utils import body_template_to_string, subject_template_to_string
from ..base.plugin import BasePlugin
from ..base.twilio import normalize_number
from contact.models import DeliveryStatus

import twilio
from twilio.rest import TwilioRestClient


class TwilioSmsContact(BasePlugin):
    def __init__(self):
        twilio_settings = settings.CONTACT_PLUGIN_TWILIO
        self.settings = twilio_settings

        self.client = TwilioRestClient(
            self.settings['account_sid'],
            self.settings['auth_token'],
        )

    def send_message(self, attempt, debug=True):
        # OK. let's ensure this is something we can handle.

        cd = attempt.contact

        from_number = self.settings['from_number']
        to_number = normalize_number(cd.value)

        obj = TwilioSMSStatus.objects.create(
            attempt=attempt,
            sent_to=cd.value,
            sent_to_normalized=to_number,
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
            attempt.mark_attempted(
                DeliveryStatus.bad_data,
                'twilio_voice',
                attempt.template
            )
            attempt.save()
            obj.save()
            return

        obj.save()

        if debug:
            return {
                "body": body,
                "subject": subject,
                "obj": obj,
            }
