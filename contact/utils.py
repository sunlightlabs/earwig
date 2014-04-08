import datetime
from django.utils.timezone import utc


def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=utc)
