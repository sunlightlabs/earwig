'''
Incoming mail and bounce requests are each handled with a webhook.
http://developer.postmarkapp.com/developer-inbound-configure.html
'''
import re

from django.conf import settings
from contact.models import DeliveryStatus
from ..base.plugin import BasePlugin

from .models import OrmDeliveryMeta


class OrmPlugin(BasePlugin):
    '''Send an email from through the postmark API.
    '''
    medium = 'email'

    def send_message(self, attempt, debug=False):
        contact_detail = attempt.contact
        self.check_contact_detail(contact_detail)

        # Mark the attempt sent.
        attempt.mark_attempted(
            status=DeliveryStatus.sent,
            plugin='database',
            template='default')

        meta = OrmDeliveryMeta.objects.create(attempt=attempt)

        if debug:
            return {
                "msg": attempt.messages.get().message.message,
            }
