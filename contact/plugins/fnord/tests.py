from django.test import TestCase
import datetime as dt

from contact.models import (
    Person,
    ContactDetail,
    Sender,
    DeliveryAttempt,
    Message,
    MessageRecipient,
    DeliveryAttempt,
)

from contact.plugins.fnord.earwig import FnordContact
from contact.plugins.fnord.models import FnordStatus

from django.db import IntegrityError


def create_test_attempt():
    pt = Person.objects.create(ocd_id='test', title='Mr.',
                          name='Paul Tagliamonte', photo_url="")
    cd = ContactDetail.objects.create(person=pt, type='fnord',
            value='@fnord', note='Fnord!', blacklisted=False)
    send = Sender.objects.create()
    message = Message(type='fnord', sender=send,
                      subject="Hello, World", message="HELLO WORLD")
    attempt = DeliveryAttempt(contact=cd, status="scheduled",
                              date=dt.datetime.utcnow(), engine="default")
    attempt.save()
    return attempt


class FnordTests(TestCase):
    def setUp(self):
        self.plugin = FnordContact()

    def test_duplicate(self):
        attempt = create_test_attempt()
        self.plugin.send_message(attempt)

        try:
            self.plugin.send_message(attempt)
            assert True is False, "We didn't get an IntegrityError out of send_message"
        except IntegrityError:
            pass
