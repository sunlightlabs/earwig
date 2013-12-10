import pytz
import unittest
import uuid
import datetime as dt

from django.test import TestCase
from django.db import IntegrityError
from django.core import serializers


from contact.models import (
    Person,
    ContactDetail,
    Sender,
    DeliveryAttempt,
    Message,
    MessageRecipient,
    DeliveryAttempt,
    Application,
)


def create_test_attempt():
    '''Creates a test attempt and all the records it requires. You
    can dump the fixture with:

        ./manage.py dumpdata contact --indent=4 > file.json
    '''
    app = Application.objects.using('test').create(
        name="Testyapp", contact="example@example.com",
        template_set="cow")

    person = Person.objects.using('test').create(
        ocd_id='test', title='Mr.',
        name='Paul Tagliamonte', photo_url="")

    contact = ContactDetail.objects.using('test').create(
        person=person, type='sms',
        value='', note='Twilio!', blacklisted=False)

    sender = Sender.objects.using('test').create(
        name="Testy McZample", id=uuid.uuid4(),
        email_expires_at=dt.datetime.now() + dt.timedelta(weeks=500))

    message = Message.objects.using('test').create(
        type='fnord', sender=sender, application=app,
        subject="Hello, World", message="HELLO WORLD")

    attempt = DeliveryAttempt.objects.using('test').create(
        contact=contact, status="scheduled",
        date=dt.datetime.now(pytz.timezone('US/Eastern')),
        engine="default")

    attempt.save()
    return attempt


if __name__ == '__main__':
    create_test_attempt()