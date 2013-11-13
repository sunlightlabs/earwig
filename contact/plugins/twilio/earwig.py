from contact.plugins import ContactPlugin
from .models import TwilioStatus
import uuid


class TwilioContact(ContactPlugin):
    def send_message(self, attempt):
        recept = uuid.uuid1()
        obj = TwilioStatus.objects.create(attempt=attempt, remote_id=recept)
        obj.save()

    def check_message_status(self, attempt):
        obj = TwilioStatus.objects.get(attempt=attempt)
        return obj.remote_id
