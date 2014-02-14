import datetime
import mock
from django.test import TestCase
from django.utils.timezone import utc
from contact.models import (Application, Sender, Person, ContactDetail, MessageRecipient,
                            MessageType, Message, ContactType, DeliveryAttempt,
                            DeliveryStatus)
from .tasks import create_delivery_attempts, process_delivery_attempt
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

    @mock.patch('engine.engines.base.send_task')
    def test_single_attempt(self, send_task):
        assert DeliveryAttempt.objects.count() == 0
        res = create_delivery_attempts.delay()
        assert res.successful()
        assert DeliveryAttempt.objects.count() == 1
        attempt = DeliveryAttempt.objects.get()
        assert attempt.contact == self.contact
        assert attempt.messages.get().message == self.msg
        send_task.assert_called_once_with('engine.tasks.process_delivery_attempt', args=(attempt,))

    @mock.patch('engine.engines.base.send_task')
    def test_only_one_attempt(self, send_task):
        # nothing should change
        res = create_delivery_attempts.delay()
        assert res.successful()
        assert DeliveryAttempt.objects.count() == 1
        res = create_delivery_attempts.delay()
        assert res.successful()
        assert DeliveryAttempt.objects.count() == 1


class TestProcessDeliveryAttempt(TestCase):

    def setUp(self):
        self.plugin = mock.Mock()

        # create DeliveryAttempt
        application = Application.objects.create(name='app', contact='fake@example.com',
                                                 template_set='')
        sender = Sender.objects.create(name='sender', email_expires_at=EXPIRY, id='1'*64)
        self.person = Person.objects.create(ocd_id='ocd-person/1', title='President',
                                            name='Gerald Fnord')
        self.vcontact = ContactDetail.objects.create(person=self.person, type=ContactType.voice,
                                                     value='202-555-5555')
        self.econtact = ContactDetail.objects.create(person=self.person, type=ContactType.email,
                                                     value='test@example.com')
        self.person.contacts.add(self.vcontact)
        self.person.contacts.add(self.econtact)
        self.msg = Message.objects.create(type=MessageType.private, sender=sender,
                                          subject='subject', message='hello everyone',
                                          application=application)
        self.mr = MessageRecipient.objects.create(recipient=self.person, message=self.msg)

        # app.conf
        app.conf.EARWIG_PLUGINS[ContactType.voice] = self.plugin
        app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
        app.conf.CELERY_ALWAYS_EAGER = True
        app.conf.BROKER_BACKEND = 'memory'

    def test_plugin_gets_called(self):
        attempt = DeliveryAttempt.objects.create(contact=self.vcontact)
        attempt.messages.add(self.mr)
        res = process_delivery_attempt.delay(attempt)
        assert res.successful()
        self.plugin.send_message.assert_called_once_with(attempt)

    def test_plugin_error(self):
        attempt = DeliveryAttempt.objects.create(contact=self.econtact)
        attempt.messages.add(self.mr)
        res = process_delivery_attempt.delay(attempt)
        assert res.successful()
        assert not self.plugin.send_message.called
