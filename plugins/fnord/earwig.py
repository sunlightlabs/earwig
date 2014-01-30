from __future__ import print_function

from ..utils import body_template_to_string, subject_template_to_string
from plugins import ContactPlugin
from .models import FnordStatus
import uuid


class FnordContact(ContactPlugin):
    def send_message(self, attempt):
        recept = uuid.uuid1()
        obj = FnordStatus.objects.create(attempt=attempt, remote_id=recept)
        obj.save()

        print("Subject:", subject_template_to_string('default', 'fnord', attempt))
        print("\n\n")
        print(body_template_to_string('default', 'fnord', attempt))
        # Will raise exception if we've done this before.
        #print("Would have sent %s" % (attempt.id))
        #print("  -> recept is %s" % (obj.remote_id))

    def check_message_status(self, attempt):
        obj = FnordStatus.objects.get(attempt=attempt)
        #print("Checking up on %s" % (obj.remote_id))
        return obj.remote_id
