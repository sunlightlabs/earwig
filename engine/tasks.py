from celery.utils.log import get_task_logger
from contact.models import MessageRecipient, DeliveryAttempt, MessageStatus
from contact.utils import utcnow
from .core import app

logger = get_task_logger(__name__)


class Engine(object):
    name = None

    def create_attempts(self, unscheduled_mrs):
        pass

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


engine = Engine()


@app.task(ignore_result=True)
def create_delivery_attempts():
    """
    This is the workhorse of earwig, looks at unscheduled MessageRecipient objects and creates
    DeliveryAttempt objects as needed
    """
    unscheduled = list(MessageRecipient.objects.filter(
        status=MessageStatus.unscheduled).order_by('recipient'))

    logger.info('sending {0} unscheduled MRs to {1}'.format(len(unscheduled), engine.name))
    engine.create_attempts(unscheduled)
