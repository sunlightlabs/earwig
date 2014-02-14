from celery.utils.log import get_task_logger
from celery.execute import send_task
from contact.models import MessageRecipient, DeliveryAttempt, MessageStatus

logger = get_task_logger(__name__)

class Engine(object):
    """
        Base class for Engines to inherit from, provides self.create_attempt
    """

    def create_attempts(self, unscheduled_mrs):
        """ should be implemented by actual engines, create attempts for each MessageRecipient """
        raise NotImplementedError('create_attempts needs to be implemented')

    def create_attempt(self, contact, messages):
        """ called by child classes, shouldn't be overridden without being extremely careful """
        # create a basic attempt
        attempt = DeliveryAttempt.objects.create(contact=contact, engine=self.__class__.__name__)
        # attach messages to it
        if isinstance(messages, MessageRecipient):
            messages = [messages]
            n = 1
        else:
            n = len(messages)

        for msg in messages:
            attempt.messages.add(msg)
            # update status
            msg.status = MessageStatus.pending
            msg.save()

        # throw this into the queue
        send_task('engine.tasks.process_delivery_attempt', args=(attempt,))
        logger.info('created DeliveryAttempt to {0} with {1} messages'.format(contact, n))
