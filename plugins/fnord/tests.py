from django.test import TestCase
from django.utils.timezone import utc
import datetime as dt
import pytz

from contact.models import (
    Person,
    ContactDetail,
    Sender,
    DeliveryAttempt,
    Message,
    MessageRecipient,
    Application,
)

from .earwig import FnordContact
from django.conf import settings
import os

from django.db import IntegrityError


def create_test_attempt():
    app = Application.objects.create(name="test", contact="fnord@fnord.fnord",
        template_set="None", active=True)

    pt = Person.objects.create(
        ocd_id='test', title='Mr.', name='Paul Tagliamonte', photo_url="")

    cd = ContactDetail.objects.create(
        person=pt, type='fnord', value='@fnord',
        note='Fnord!', blacklisted=False)

    send = Sender.objects.create(
        id='randomstring', email_expires_at=dt.datetime(2020, 1, 1, tzinfo=utc))

    message = Message(
        type='fnord', sender=send, subject="Hello, World",
        message="HELLO WORLD", application=app)

    message.save()

    mr = MessageRecipient(message=message, recipient=pt, status='pending')
    mr.save()

    attempt = DeliveryAttempt(
        contact=cd, status="scheduled",
        template='fnord-testing-deterministic-name',
        date=dt.datetime.now(pytz.timezone('US/Eastern')),
        engine="default")

    attempt.save()
    attempt.messages.add(mr)
    return attempt


class FnordTests(TestCase):
    def setUp(self):
        self.plugin = FnordContact()

        # beyond this, we also need to mangle the path pretty bad.
        # so that we have our test templates set and nothing else. We'll
        # fix this after for the other tests.
        self._templates = settings.TEMPLATE_DIRS
        settings.TEMPLATE_DIRS = (
            os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         '..', 'test_templates')),
        )

    def tearDown(self):
        settings.TEMPLATE_DIRS = self._templates


    def test_duplicate(self):
        """ Ensure that we blow up with two identical inserts """
        attempt = create_test_attempt()
        self.plugin.send_message(attempt, debug=True)

        try:
            self.plugin.send_message(attempt, debug=True)
            assert True is False, ("We didn't get an IntegrityError out of "
                                   "send_message")
        except IntegrityError:
            pass

    def test_status(self):
        """ Ensure that we can properly fetch the status out of the DB """
        plugin = FnordContact()
        attempt = create_test_attempt()
        plugin.send_message(attempt, debug=True)
        id1 = plugin.check_message_status(attempt)

        plugin = FnordContact()
        id2 = plugin.check_message_status(attempt)

        assert id1 == id2, ("We got a different result from a check when"
                            " given a new plugin object. DB issue?")

    def test_message(self):
        plugin = FnordContact()
        attempt = create_test_attempt()
        debug_info = plugin.send_message(attempt, debug=True)
        assert debug_info['subject'] == ''
        assert debug_info['body'] == """green blue red blue red green green


    HELLO WORLD

"""
