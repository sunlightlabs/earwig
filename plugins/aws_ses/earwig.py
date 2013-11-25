import uuid

import boto.ses

from ..utils import template_to_string
from .models import SESDeliveryMeta
from .. import EmailContactPlugin


class SESContact(EmailContactPlugin):
    '''Amazon SES contact plugin.

    Bounce requests would be configured with SNS:
    http://aws.amazon.com/about-aws/whats-new/2012/06/26/amazon-ses-announces-bounce-and-complaint-notifications/

    The alternative is setting up a special address to reveive them
    by email, which would suck.
    '''
    medium = 'email'

    def send_message(self, attempt, extra_context=None):
        self.check_contact_detail(attempt)
        contact_detail = attempt.contact
        email_address = contact_detail.value

        body_template = self.get_body_template(attempt)
        subject_template = self.get_subject_template(attempt)

        message = body_template.render(attempt=attempt, **extra_context or {})
        subject = subject_template.render(attempt=attempt, **extra_context or {})

        conn = boto.ses.connect_to_region()
        resp = conn.send_email(
             source=self.get_sender_address(attempt),
             subject=subject,
             body=body,
             to_addresses=[email_address],
             reply_addresses=self.get_reply_addreses(attempt))

        request_id = resp['SendEmailResponse']['ResponseMetadata']['RequestID']
        message_id = resp['SendEmailResult']['MessageId']
        obj = SentEmailStatus.create(
            attempt=attempt, request_id=request_id, message_id=message_id)

    def check_message_status(self, attempt):
        '''This function depends on shape of SNS notifactions and
        the output we want from this funtion.
        '''
        obj = SESDeliveryMetadata.get(attempt=attempt)
        raise NotImplementedError()
