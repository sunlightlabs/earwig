'''Sendgrid handles incoming email and unsubscribe/bounce
 with webhooks. You set up a endpoints and they post data to them.
 http://sendgrid.com/docs/API_Reference/Webhooks/index.html
'''
import sendgrid

from ..plugins import ContactPlugin
from .models import SendgridDeliveryMeta


class SendgridContact(ContactPlugin):
    '''Send an email from through the postmark API.
    '''
    medium = 'email'

    def send_message(self, attempt, extra_context=None):
        contact_detail = attempt.contact
        recipient_email_address = contact_detail.value

        body_template = self.get_body_template(attempt)
        subject_template = self.get_subject_template(attempt)

        message = body_template.render(attempt=attempt, **extra_context or {})
        subject = subject_template.render(attempt=attempt, **extra_context or {})

        api = sendgrid.Sendgrid(
            settings.SENDGRID_USERNAME,
            settings.SENDGRID_PASSWORD,
            secure=True)

        message = sendgrid.Message(
            self.get_sender(attempt),
            subject,
            message)
        message.add_tp(recipient_email_address)

        response = api.web.send(message)
        message_id = response['MessageID']
        SendgridDeliveryMeta.create(attempt=attempt, message_id=message_id)

    def check_message_status(self, attempt):
        obj = SendgridDeliveryMetad.get(attempt=attempt)
        response = pystmark.get_bounces(settings.POSTMARK_API_KEY)
        for bounce in response.json()['Bounces']:
            if bounce['MessageID'] == obj.message_id:
                return EmailDeliveryStatus(bounce['Type'], bounce)