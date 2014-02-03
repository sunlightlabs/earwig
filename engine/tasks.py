from celery.utils.log import get_task_logger
from contact.models import MessageRecipient, DeliveryAttempt
from .core import app

logger = get_task_logger(__name__)

class Engine(object):
    name = None

    def create_attempts(unscheduled_mrs):
        pass


engine = Engine()

@app.task(ignore_result=True)
def create_delivery_attempts():
    """
    This is the workhorse of earwig, looks at unscheduled MessageRecipient objects and creates
    DeliveryAttempt objects as needed
    """
    unscheduled = list(MessageRecipient.objects.filter(status='unscheduled').order_by('recipient'))

    logger.info('sending {0} unscheduled MRs to {1}'.format(len(unscheduled), engine.name))
    engine.create_attempts(unscheduled)
