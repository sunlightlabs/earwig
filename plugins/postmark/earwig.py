'''
Incoming mail and bounce requests are each handled with a webhook.
http://developer.postmarkapp.com/developer-inbound-configure.html
'''
import pystmark

from ..plugins import ContactPlugin, EmailDeliveryStatus
from .models import PostmarkDeliveryMeta


class PostmarkContact(ContactPlugin):
    '''Send an email from through the postmark API.
    '''
    def send_message(self, attempt, extra_context=None):
        contact_detail = attempt.contact
        recipient_email_address = contact_detail.value

        body_template = self.get_body_template(attempt)
        subject_template = self.get_subject_template(attempt)

        message = body_template.render(attempt=attempt, **extra_context or {})
        subject = subject_template.render(attempt=attempt, **extra_context or {})

        message = pystmark.Message(
            sender=self.get_sender(attempt),
            to=recipient_email_address,
            subject=subject,
            text=message
            )
        response = pystmark.send(message, api_key=settings.POSTMARK_API_KEY)
        message_id = response['MessageID']
        PostmarkDeliveryMetad.create(attempt=attempt, message_id=message_id)

    def check_message_status(self, attempt):
        obj = PostmarkDeliveryMetad.get(attempt=attempt)
        response = pystmark.get_bounces(settings.POSTMARK_API_KEY)
        for bounce in response.json()['Bounces']:
            if bounce['MessageID'] == obj.message_id:
                return EmailDeliveryStatus(bounce['Type'], bounce)