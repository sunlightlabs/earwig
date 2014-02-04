from celery.utils.log import get_task_logger
from contact.models import MessageRecipient, DeliveryAttempt, MessageStatus
from contact.utils import utcnow

class Engine(object):
    name = None

    def create_attempts(self, unscheduled_mrs):
        raise NotImplementedError('create_attempts needs to be implemented')

    def create_attempt(self, contact, message, plugin, template):
        attempt = DeliveryAttempt.objects.create(contact=contact, engine=self.name, plugin=plugin,
                                                 template=template, updated_at=utcnow())
        if isinstance(message, MessageRecipient):
            attempt.messages.add(message)
        elif isinstance(message, list):
            for msg in message:
                attempt.messages.add(message)


class DumbEngine(object):
    """
        a dumb proof-of-concept engine that creates a delivery attempt to the first available
        contact
    """

    name = 'dumb'

    def create_attempts(self, unscheduled_mrs):
        for mr in unscheduled_mrs:
            first_contact = mr.contacts.all()[0]
            self.create_attempt(first_contact, mr, '?', '?')
