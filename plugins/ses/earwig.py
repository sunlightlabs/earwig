import boto.ses

from django.conf import settings

from ..utils import body_template_to_string, subject_template_to_string
from .models import SESDeliveryMeta
from ..base.plugin import BasePlugin


class SESContact(BasePlugin):
    '''Amazon SES contact plugin.

    Bounce requests would be configured with SNS:
    http://aws.amazon.com/about-aws/whats-new/2012/06/26/amazon-ses-announces-bounce-and-complaint-notifications/

    The alternative is setting up a special address to receive them
    by email, which would suck.
    '''
    medium = 'email'

    def send_message(self, attempt, debug=True):
        contact_detail = attempt.contact
        self.check_contact_detail(contact_detail)
        recipient_email_address = contact_detail.value

        body = body_template_to_string(attempt.template, 'email', attempt)
        subject = subject_template_to_string(attempt.template, 'email', attempt)

        conn = boto.ses.connect_to_region()
        resp = conn.send_email(
            source=settings.EARWIG_EMAIL_SENDER,
            subject=subject,
            body=body,
            to_addresses=[recipient_email_address],

            # This may need to change.
            reply_addresses=settings.EARWIG_EMAIL_SENDER)

        request_id = resp['SendEmailResponse']['ResponseMetadata']['RequestID']
        message_id = resp['SendEmailResult']['MessageId']
        meta = SESDeliveryMeta.objects.create(
            attempt=attempt, message_id=message_id)

        if debug:
            return {
                "body": body,
                "subject": subject,
                "obj": meta
            }
