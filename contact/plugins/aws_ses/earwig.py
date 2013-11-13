import uuid

import boto.ses

from .models import SESEmailStatus
from contact.plugins import ContactPlugin


class SESContact(ContactPlugin):
    '''Amazon SES contact plugin.

    Requires some settings, in addition to usual AWS config:
     - Sender address
     - Reply-to address, mailbox with a scheduled processing job, etc.
     - Return path, a mailbox for processing bounce requests, updating
       contact blacklisting, etc. Though bounce/complaints can also be
       recieved through SNS.
    - separate bounce address for tests versus production?

     Things that may need to be passed in: a jinja2 message template.

     Tests this probably needs:
        - verify no message sent to blacklisted address
        - verify bounce/complaints get handled correctly
        - verify undeliverable gets handled correctly
    '''
    def send_message(self, attempt, body_template, subject_template, extra_context=None):

        contact_detail = attempt.contact
        assert contact_detail.type == 'email'
        assert not contact_detail.blacklisted
        email_address = contact_detail.value

        message = body_template.render(attempt=attempt, **extra_context or {})
        subject = subject_template.render(attempt=attempt, **extra_context or {})

        conn = boto.ses.connect_to_region()
        resp = conn.send_email(
             source=settings.PLUGIN_EMAIL_SES_SENDER_ADDRESS,
             subject=subject,
             body=body,
             to_addresses=[email_address],
             # bcc_addresses=people_who_requested_contact,

             # This is the address we want the person to reply to.
             reply_addresses=settings.PLUGIN_EMAIL_SES_REPLY_ADDRESSES,

             # The email address to which bounce notifications are forwarded.
             return_path=settings.PLUGIN_EMAIL_SES_RETURN_PATH)

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
        print("Checking up on %s" % (obj.remote_id))
