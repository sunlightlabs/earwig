from __future__ import print_function
from django.conf import settings
from django.core.urlresolvers import reverse

from ..base.plugin import BasePlugin
from .models import TwilioVoiceStatus
from contact.models import DeliveryStatus
from .views import intro

import twilio
from twilio.rest import TwilioRestClient


class TwilioVoiceContact(BasePlugin):
    medium = 'voice'

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

        obj = TwilioVoiceStatus.objects.create(
            attempt=attempt,
            sent_to=cd.value,
            sent_from=from_number,
            sent=False
        )
        obj.save()

        callback_url = "{0}{1}".format(
            settings.EARWIG_PUBLIC_LINK_ROOT,
            reverse(intro, args=[attempt.id]),
        )

        try:
            self.client.calls.create(to=cd.value,
                                     from_=from_number,
                                     IfMachine="Continue",
                                     url=callback_url)
            # OK. We're not marking it as sent, since we're not actually
            # confirming that it's been sent until we get the callback
            # from the actual phonecall. We set it to sent in the view.
        except twilio.TwilioRestException:
            attempt.mark_attempted(
                DeliveryStatus.bad_data,
                'twilio_voice',
                attempt.template
            )
            attempt.save()
            return
