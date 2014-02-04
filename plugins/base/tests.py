import os
import datetime
from django.utils.timezone import utc
from django.conf import settings
from django.db import IntegrityError
from contact.models import (Person, ContactDetail, Sender, DeliveryAttempt, Message,
                            MessageRecipient, Application)


def create_test_attempt():
    app = Application.objects.create(name="test", contact="fnord@fnord.fnord",
                                     template_set="None", active=True)

    pt = Person.objects.create(ocd_id='test', title='Mr.', name='Paul Tagliamonte', photo_url="")

    cd = ContactDetail.objects.create(person=pt, type='fnord', value='@fnord',
                                      note='fnord!', blacklisted=False)

    send = Sender.objects.create(id='randomstring',
                                 email_expires_at=datetime.datetime(2020, 1, 1, tzinfo=utc))

    message = Message.objects.create(type='fnord', sender=send, subject="Hello, World",
                                     message="HELLO WORLD", application=app)

    mr = MessageRecipient.objects.create(message=message, recipient=pt, status='pending')

    attempt = DeliveryAttempt.objects.create(contact=cd, status="scheduled",
                                             template='fnord-testing-deterministic-name',
                                             engine="default")
    attempt.messages.add(mr)
    return attempt


class BaseTests(object):
    def setUp(self):
        super(BaseTests, self).setUp()
        self._template_dirs = settings.TEMPLATE_DIRS
        settings.TEMPLATE_DIRS = (
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test_templates')),
        )
        self.attempt = create_test_attempt()

    def tearDown(self):
        super(BaseTests, self).tearDown()
        settings.TEMPLATE_DIRS = self._template_dirs

    def test_duplicate(self):
        """ Ensure that we blow up with two identical inserts """
        self.plugin.send_message(self.attempt, debug=True)

        with self.assertRaises(IntegrityError):
            self.plugin.send_message(self.attempt, debug=True)
