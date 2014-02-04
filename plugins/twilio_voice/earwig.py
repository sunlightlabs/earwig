from __future__ import print_function
from django.conf import settings
from django.core.urlresolvers import reverse

from contact.errors import InvalidContactValue
from ..utils import body_template_to_string, subject_template_to_string
from .. import ContactPlugin
from .models import TwilioVoiceStatus
from .views import call

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

        obj = TwilioVoiceStatus.objects.create(
            attempt=attempt,
            sent_to=cd.value,
            sent_from=from_number,
            sent=False
        )
        # We're going to save this record and only actually issue the sent
        # when we get the callback from the Twilio service.
        obj.save()

        callback_url = "{0}{1}".format(
            settings.EARWIG_PUBLIC_LINK_ROOT,
            reverse(call, args=[obj.id]),
        )

        try:
            twilio_call = self.client.calls.create(to=cd.value,
                                                   from_=from_number,
                                                   url=callback_url)
        except twilio.TwilioRestException as e:
            raise InvalidContactValue("Contact detail value seems wrong")

    def check_message_status(self, attempt):
        obj = TwilioVoiceStatus.objects.get(attempt=attempt)
        return "sent" if obj.sent else "failed"
