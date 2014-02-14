import datetime
import mock
from django.test import TestCase
from django.utils.timezone import utc
from contact.models import (Application, Sender, Person, ContactDetail, MessageRecipient,
                            MessageType, Message, ContactType, DeliveryAttempt)
from ..tasks import create_delivery_attempts, process_delivery_attempt
from .newengine import NewEngine
from ..core import app

EXPIRY = datetime.datetime(2020, 1, 1, tzinfo=utc)


class TestNewEngineIdeas(TestCase):

    def tearDown(self):
        app.conf.ENGINE = self._old_engine

    def setUp(self):
        self.plugin = mock.Mock()
        self._old_engine = app.conf.ENGINE
        app.conf.ENGINE = NewEngine()

        # create DeliveryAttempt
        application = Application.objects.create(name='app', contact='fake@example.com',
                                                 template_set='')
        sender = Sender.objects.create(name='sender', email_expires_at=EXPIRY, id='1'*64)


        fnord = Person.objects.create(ocd_id='ocd-person/1', title='President',
                                      name='Gerald Fnord')
        vcontact = ContactDetail.objects.create(person=fnord, type=ContactType.voice,
                                                value='202-555-5555')
        econtact = ContactDetail.objects.create(person=fnord, type=ContactType.email,
                                                value='test@example.com')
        fnord.contacts.add(vcontact)
        fnord.contacts.add(econtact)


        rob_fnord = Person.objects.create(ocd_id='ocd-person/2', title='Mayor',
                                          name='Rob Fnord')
        vcontact = ContactDetail.objects.create(person=rob_fnord, type=ContactType.voice,
                                                value='202-555-6666')
        rob_fnord.contacts.add(vcontact)


        henry_fnord = Person.objects.create(ocd_id='ocd-person/3', title='Mr.',
                                            name='Henry Fnord')
        # No contact information.


        for person in [fnord, rob_fnord, henry_fnord]:
            for message in range(5):
                msg = Message.objects.create(type=MessageType.private, sender=sender,
                                       subject='subject', message='hello everyone',
                                       application=application)
                mr = MessageRecipient.objects.create(recipient=person,
                                                     message=msg)

        # app.conf
        app.conf.EARWIG_PLUGINS[ContactType.voice] = self.plugin
        app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
        app.conf.CELERY_ALWAYS_EAGER = True
        app.conf.BROKER_BACKEND = 'memory'

    def test_delivery_attempts(self):
        # nothing should change
        assert MessageRecipient.objects.count() == 15
        # Right, OK

        res = create_delivery_attempts.delay()
        das = DeliveryAttempt.objects.all()
        assert len(das) == 10  # 5 email, 5 voice, 5 undeliverable

        assert DeliveryAttempt.objects.filter(
            contact__type=ContactType.voice
        ).count() == 5

        assert DeliveryAttempt.objects.filter(
            contact__type=ContactType.email
        ).count() == 5
