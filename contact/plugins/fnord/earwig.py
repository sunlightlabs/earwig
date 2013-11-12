from contact.plugins import ContactPlugin
from .models import FnordStatus
import uuid


class FnordContact(ContactPlugin):
    def send_message(self, attempt):
        recept = uuid.uuid1()
        obj = FnordStatus.create(attempt=attempt, remote_id=recept)
        # Will raise exception if we've done this before.
        print("Would have sent %s" % (attempt.id))
        print("  -> recept is " % (obj.remote_id))

    def check_message_status(self, attempt):
        obj = FnordStatus.get(attempt=attempt)
        print("Checking up on %s" % (obj.remote_id))
