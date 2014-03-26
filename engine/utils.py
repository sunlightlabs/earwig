from django.conf import settings
import logging

logger = logging.getLogger('earwig')


def notify_admins(tag, body):
    if not settings.DEBUG:
        # Send some email using postmark?
        pass

    logger.warning("Notification: %s: %s" % (tag, body))
