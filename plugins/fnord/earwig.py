from ..utils import body_template_to_string, subject_template_to_string
from ..base.plugin import BasePlugin
from .models import FnordStatus
import uuid


class FnordContact(BasePlugin):
    def send_message(self, attempt, debug=False):
        receipt = uuid.uuid1()
        obj = FnordStatus.objects.create(attempt=attempt, remote_id=receipt)
        obj.save()

        subject = subject_template_to_string(attempt.template, 'fnord', attempt)
        body = body_template_to_string(attempt.template, 'fnord', attempt)

        if debug:
            return {
                "subject": subject,
                "body": body,
                "obj": obj,
            }

        # write to a file
        with open('fnord-{0}.txt'.format(receipt), 'w') as fh:
            fh.write("Subject: {0}\n\n\n{1}".format(subject, body))

    def check_message_status(self, attempt):
        obj = FnordStatus.objects.get(attempt=attempt)
        return obj.remote_id
