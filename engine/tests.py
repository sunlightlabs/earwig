import datetime
import mock
import celery
from django.test import TestCase
from django.utils.timezone import utc
from contact.models import (Application, Sender, Person, ContactDetail, MessageRecipient,
                            MessageType, Message, ContactType, DeliveryAttempt)
from .tasks import create_delivery_attempts
from .core import app

EXPIRY = datetime.datetime(2020, 1, 1, tzinfo=utc)


class TestCreateDeliveryAttempts(TestCase):
    def setUp(self):
        application = Application.objects.create(name='app', contact='fake@example.com',
                                                 template_set='')
        sender = Sender.objects.create(name='sender', email_expires_at=EXPIRY, id='1'*64)
        person = Person.objects.create(ocd_id='ocd-person/1', title='President',
                                       name='Gerald Fnord')
        self.contact = ContactDetail.objects.create(person=person, type=ContactType.voice,
                                                    value='202-555-5555')
        person.contacts.add(self.contact)
        self.msg = Message.objects.create(type=MessageType.private, sender=sender,
                                          subject='subject', message='hello everyone',
                                          application=application)
        MessageRecipient.objects.create(recipient=person, message=self.msg)

        app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
        app.conf.CELERY_ALWAYS_EAGER = True
        app.conf.BROKER_BACKEND = 'memory'

    @mock.patch('engine.engines.send_task')
    def test_single_attempt(self, send_task):
        assert DeliveryAttempt.objects.count() == 0
        res = create_delivery_attempts.delay()
        assert res.successful()
        assert DeliveryAttempt.objects.count() == 1
        attempt = DeliveryAttempt.objects.get()
        assert attempt.contact == self.contact
        assert attempt.messages.get().message == self.msg
        # assert_called_once_with fails for some unknown reason
        assert send_task.call_count == 1
        assert send_task.call_args == (('engine.tasks.process_delivery_attempt',), {'args': (attempt,)})

    @mock.patch('engine.engines.send_task')
    def test_only_one_attempt(self, send_task):
        # nothing should change
        res = create_delivery_attempts.delay()
        assert res.successful()
        assert DeliveryAttempt.objects.count() == 1
        res = create_delivery_attempts.delay()
        assert res.successful()
        assert DeliveryAttempt.objects.count() == 1
