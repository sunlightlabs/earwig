import uuid

import boto.ses

from .models import SESEmailStatus
from .. import ContactPlugin


class SESContact(ContactPlugin):
    '''Amazon SES contact plugin.

    Bounce requests would be configured with SNS:
    http://aws.amazon.com/about-aws/whats-new/2012/06/26/amazon-ses-announces-bounce-and-complaint-notifications/

    The alternative is setting up a special address to reveive them
    by email, which would suck.

    Tests this probably needs:
        - verify no message sent to blacklisted address
        - verify bounce/complaints get handled correctly
        - verify undeliverable gets handled correctly
    '''
    def send_message(self, attempt, extra_context=None):

        assert contact_detail.type == 'email'
        assert not contact_detail.blacklisted
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
             # bcc_addresses=people_who_requested_contact, ?
             reply_addresses=self.get_reply_addreses(attempt)
             )

        request_id = resp['SendEmailResponse']['ResponseMetadata']['RequestID']
        message_id = resp['SendEmailResult']['MessageId']
        obj = SentEmailStatus.create(
            attempt=attempt, request_id=request_id, message_id=message_id)

    def check_message_status(self, attempt):
        '''To do this, we need to set up an email address to recieve bounce
        requests and a job to process the messages in the mail box and update
        their SESEmailStatus.
        '''
        obj = SESEmailStatus.get(attempt=attempt)
        # maybe return some JSON? print("Checking up on %s" % (obj.remote_id))

    def get_body_template(self, attempt):
        raise NotImplementedError()

    def get_subject_template(self, attempt):
        raise NotImplementedError()

    def get_sender_address(self, attempt):
        raise NotImplementedError()

    def get_reply_addreses(self, attempt):
        raise NotImplementedError()
