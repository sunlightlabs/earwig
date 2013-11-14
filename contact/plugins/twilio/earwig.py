from django.conf import settings

from contact.errors import InvalidContactType, InvalidContactValue
from contact.plugins import ContactPlugin
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
        if cd.type not in ['sms',]:
            raise InvalidContactType("Contact Detail type is not `sms`")

        from_number = self.settings['from_number']

        obj = TwilioStatus.objects.create(
            attempt=attempt,
            sent_to=cd.value,
            sent_from=from_number,
            sent=False
        )

        body = "This will be from a template"

        try:
            self.client.messages.create(to=cd.value,
                                        from_=from_number,
                                        body=body)
            obj.sent = True
        except twilio.TwilioRestException as e:
            print e
            raise InvalidContactValue("Contact detail value seems wrong")

        obj.save()

    def check_message_status(self, attempt):
        obj = TwilioStatus.objects.get(attempt=attempt)
        return "sent" if obj.sent else "failed"
