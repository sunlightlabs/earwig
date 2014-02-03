'''
Incoming mail and bounce requests are each handled with a webhook.
http://developer.postmarkapp.com/developer-inbound-configure.html
'''
import pystmark

from django.conf import settings

from .. import ContactPlugin, EmailDeliveryStatus
from ..utils import body_template_to_string, subject_template_to_string
from .models import PostmarkDeliveryMeta


class PostmarkContact(ContactPlugin):
    '''Send an email from through the postmark API.
    '''
    def send_message(self, attempt, debug=False):
        contact_detail = attempt.contact
        recipient_email_address = contact_detail.value

        body = body_template_to_string(attempt.template, 'email', attempt)
        subject = subject_template_to_string(attempt.template, 'email', attempt)

        message = pystmark.Message(
            sender=settings.EARWIG_EMAIL_SENDER,
            to=recipient_email_address,
            subject=subject,
            text=body)

        api_key = getattr(settings, 'POSTMARK_API_KEY', None)
        response = pystmark.send(message, api_key)
        resp_json = response.json()
        message_id = resp_json['MessageID']
        meta = PostmarkDeliveryMeta.objects.create(
            attempt=attempt, message_id=message_id)

        if debug:
            return {
                "body": body,
                "subject": subject,
                "obj": meta }

    def check_message_status(self, attempt):
        obj = PostmarkDeliveryMeta.get(attempt=attempt)
        response = pystmark.get_bounces(settings.POSTMARK_API_KEY)
        for bounce in response.json()['Bounces']:
            if bounce['MessageID'] == obj.message_id:
                return EmailDeliveryStatus(bounce['Type'], bounce)
