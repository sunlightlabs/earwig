from contact.plugins import ContactPlugin
from .models import TwilioStatus
from twilio.rest import TwilioRestClient


class TwilioContact(ContactPlugin):
    def __init__(self):
        # XXX: How do we get these?
        self.client = TwilioRestClient(account_sid, auth_token)

    def send_message(self, attempt):
        obj = TwilioStatus.objects.create(
            attempt=attempt,
            sent_to=to_number,
            sent_from=from_number,
            sent=False
        )

        try:
            client.messages.create(to=to_number,
                                   from_=from_number,
                                   body=body)
            obj.sent = True
        except twilio.TwilioRestException:
            pass # XXX: Capture what's gone wrong here. Invalid? Down?

        obj.save()

    def check_message_status(self, attempt):
        obj = TwilioStatus.objects.get(attempt=attempt)
        return obj.remote_id
