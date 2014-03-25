from celery.utils.log import get_task_logger
from contact.models import MessageRecipient, MessageStatus
from celery import Task
from .core import app

logger = get_task_logger(__name__)


class EngineTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # In the future, some code will go here to notify us that something
        # has gone wrong with this task (but not swamp our stuff), or perhaps
        # call raven and tell sentery that something's gone wrong. This method
        # is a massive pain to debug, since all stdout / logging messages
        # from here seem to get squashed (but stuff like NameError triggers
        # an exception)
        pass


@app.task(ignore_result=True, base=EngineTask)
def create_delivery_attempts():
    """
    Looks at unscheduled MessageRecipient objects and creates DeliveryAttempt objects as needed.
    """
    unscheduled = list(MessageRecipient.objects.filter(
        status=MessageStatus.unscheduled).order_by('recipient'))

    n = len(unscheduled)
    if n:
        logger.info('sending {0} unscheduled MRs to {1}'.format(
            n, app.conf.ENGINE.__class__.__name__))
        app.conf.ENGINE.create_attempts(unscheduled)
    else:
        logger.debug('no unscheduled MRs to dispatch')


@app.task(ignore_result=True, bind=True, base=EngineTask)
def process_delivery_attempt(self, attempt):
    """
    Send a delivery attempt using the active plugin.
    """

    try:
        plugin = app.conf.EARWIG_PLUGINS[attempt.contact.type]
    except KeyError as exc:
        logger.error('no plugin for {0} ({1} not delivered)'.format(attempt.contact.type, attempt))
        raise self.retry(exc=exc, countdown=0)
        # Retry the task in 2 minutes; don't spam the system.

    logger.info('processing {0} with {1}'.format(attempt, plugin.__class__.__name__))
    plugin.send_message(attempt)
