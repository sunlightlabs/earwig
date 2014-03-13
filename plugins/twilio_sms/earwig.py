from __future__ import print_function
from django.conf import settings

from .models import TwilioSMSStatus
from ..utils import (body_template_to_string, subject_template_to_string,
                     intro_template_to_string)
from ..base.plugin import BasePlugin
from ..base.twilio import normalize_number
from contact.models import DeliveryStatus

import twilio
from twilio.rest import TwilioRestClient


class TwilioSmsContact(BasePlugin):
    medium = 'sms'

    def __init__(self):
        twilio_settings = settings.CONTACT_PLUGIN_TWILIO
        self.settings = twilio_settings

        self.client = TwilioRestClient(
            self.settings['account_sid'],
            self.settings['auth_token'],
        )

    def send_message(self, attempt, debug=True):
        cd = attempt.contact

        self.check_contact_detail(cd)

        from_number = self.settings['from_number']
        to_number = normalize_number(cd.value)

        prior_attempts = TwilioSMSStatus.objects.filter(
            sent_to=to_number
        ).count()

        needs_intro = (prior_attempts == 0)

        if needs_intro:
            intro = intro_template_to_string(attempt.template, 'sms', attempt)
            try:
                self.client.messages.create(to=cd.value,
                                            from_=from_number,
                                            body=intro)
            except twilio.TwilioRestException:
                # Uhhh... Let's handle this below where we can do some record
                # keeping.
                pass

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
            attempt.mark_attempted(
                DeliveryStatus.sent,
                'twilio_sms',
                attempt.template
            )
        except twilio.TwilioRestException:
            attempt.mark_attempted(
                DeliveryStatus.bad_data, 'twilio_sms', attempt.template)
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
