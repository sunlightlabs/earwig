import pystmark

from .plugins import ContactPlugin
from .models import PostmarkEmailStatus


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
        PostmarkEmailStatus.create(attempt=attempt, message_id=message_id)


    def check_message_status(self, attempt):
        '''To do this, we need to set up an email address to recieve bounce
        requests and a job to process the messages in the mail box and update
        their SESEmailStatus.
        '''
        obj = PostmarkEmailStatus.get(attempt=attempt)
        response = pystmark.get_bounces(settings.POSTMARK_API_KEY)
        for bounce in response.json()['Bounces']:
            if bounce['MessageID'] == attempt.message_id:
                return 'cow'

    def get_body_template(self, attempt):
        raise NotImplementedError()

    def get_subject_template(self, attempt):
        raise NotImplementedError()

    def get_sender_address(self, attempt):
        raise NotImplementedError()

    def get_reply_addreses(self, attempt):
        raise NotImplementedError()
