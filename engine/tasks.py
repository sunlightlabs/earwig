from celery.utils.log import get_task_logger
from contact.models import MessageRecipient, MessageStatus
from .core import app

logger = get_task_logger(__name__)


@app.task(ignore_result=True)
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


@app.task(ignore_result=True)
def process_delivery_attempt(attempt):
    """
    Send a delivery attempt using the active plugin.
    """
    try:
        plugin = app.conf.EARWIG_PLUGINS[attempt.contact.type]
        logger.info('processing {0} with {1}'.format(attempt, plugin.__class__.__name__))
        plugin.send_message(attempt)
    except KeyError:
        logger.error('no plugin for {0} ({1} not delivered)'.format(attempt.contact.type, attempt))
        # XXX: do more here than log?
