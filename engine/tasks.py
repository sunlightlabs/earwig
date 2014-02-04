from celery.utils.log import get_task_logger
from contact.models import MessageRecipient, DeliveryAttempt, MessageStatus
from contact.utils import utcnow
from .core import app

logger = get_task_logger(__name__)


engine = Engine()


@app.task(ignore_result=True)
def create_delivery_attempts():
    """
    Looks at unscheduled MessageRecipient objects and creates DeliveryAttempt objects as needed.
    """
    unscheduled = list(MessageRecipient.objects.filter(
        status=MessageStatus.unscheduled).order_by('recipient'))

    logger.info('sending {0} unscheduled MRs to {1}'.format(len(unscheduled), engine.name))
    engine.create_attempts(unscheduled)


@app.task(ignore_result=True)
def process_delivery_attempts():
    """
    Looks through scheduled delivery attempts and dispatches them to the active plugin.
    """
