from ..utils import body_template_to_string, subject_template_to_string
from plugins import ContactPlugin
from .models import FnordStatus
import uuid


class FnordContact(ContactPlugin):
    def send_message(self, attempt):
        receipt = uuid.uuid1()
        obj = FnordStatus.objects.create(attempt=attempt, remote_id=receipt)
        obj.save()

        # write to a file
        with open('fnord-{0}.txt'.format(receipt), 'w') as fh:
            fh.write("Subject: {0}\n\n\n{1}".format(
                subject_template_to_string('default', 'fnord', attempt),
                body_template_to_string('default', 'fnord', attempt)
            ))

    def check_message_status(self, attempt):
        obj = FnordStatus.objects.get(attempt=attempt)
        return obj.remote_id
