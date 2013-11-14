from django.conf import settings

from contact.errors import InvalidContactType, InvalidContactValue
from contact.plugins import ContactPlugin
from .models import TwilioStatus
from twilio.rest import TwilioRestClient


class TwilioContact(ContactPlugin):
    def __init__(self):
        # XXX: How do we get these?
        twilio_settings = settings.CONTACT_PLUGIN_TWILIO

        self.client = TwilioRestClient(
            twilio_settings['account_sid'],
            twilio_settings['auth_token'],
        )

    def send_message(self, attempt):
        # OK. let's ensure this is something we can handle.

        cd = attempt.contact
        if cd.type not in ['sms',]:
            raise InvalidContactType("Contact Detail type is not `sms`")

        obj = TwilioStatus.objects.create(
            attempt=attempt,
            sent_to=to_number,
            sent_from=from_number,
            sent=False
        )

        try:
            client.messages.create(to=to_number,
                                   from_=from_number,
                                   body=body)
            obj.sent = True
        except twilio.TwilioRestException:
            raise InvalidContactValue("Contact detail value seems wrong")

        obj.save()

    def check_message_status(self, attempt):
        obj = TwilioStatus.objects.get(attempt=attempt)
        return obj.remote_id
