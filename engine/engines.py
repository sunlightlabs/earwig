from celery.utils.log import get_task_logger
from celery.execute import send_task
from contact.models import MessageRecipient, DeliveryAttempt

logger = get_task_logger(__name__)


class Engine(object):
    name = None

    def create_attempts(self, unscheduled_mrs):
        """ should be implemented by actual engines, create attempts for each MessageRecipient """
        raise NotImplementedError('create_attempts needs to be implemented')

    def create_attempt(self, contact, message, plugin, template):
        """ called by child classes, shouldn't be overridden without being extremely careful """
        # create a basic attempt
        attempt = DeliveryAttempt.objects.create(contact=contact, engine=self.name, plugin=plugin,
                                                 template=template)
        # attach messages to it
        if isinstance(message, MessageRecipient):
            attempt.messages.add(message)
            n = 1
        elif isinstance(message, list):
            n = len(list)
            for msg in message:
                attempt.messages.add(message)

        # throw this into the queue
        send_task('engine.tasks.process_delivery_attempt', args=(attempt,))

        logger.info('created DeliveryAttempt to {0} with {1} messages'.format(contact, n))


class DumbEngine(Engine):
    """
        a dumb proof-of-concept engine that creates a delivery attempt to the first available
        contact
    """

    name = 'dumb'

    def create_attempts(self, unscheduled_mrs):
        for mr in unscheduled_mrs:
            first_contact = mr.contacts.all()[0]
            self.create_attempt(first_contact, mr, '?', '?')
