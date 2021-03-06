import datetime
import mock
from django.test import TestCase
from django.utils.timezone import utc
from contact.models import (Application, Sender, Person, ContactDetail, MessageRecipient,
                            MessageType, Message, ContactType, DeliveryAttempt,
                            DeliveryStatus)
from ..tasks import create_delivery_attempts, process_delivery_attempt
from .newengine import NewEngine
from .dumbsmartengine import DumbSmartEngine
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

    @mock.patch('engine.engines.base.send_task')
    def test_delivery_attempts(self, send_task):
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


class TestDumbSmartEngine(TestCase):
    '''Tests the following things:

    - If a prior message was successully delivered:
      - schedules another message only if the engine-defined nag_period has
        not elapsed since the succesful delivery.
        - Requires: Prior successful Attempts within nag_period.
      - If the nag period has elapsed, picks a different contact detail to
        send the message to.
        - Requires: Prior sucessful attempt and 2 contact types.
    - If a mr has prior failed delivery attempts, and the failures were
      due to bad/invalid contact details, the engine will try to  choose
      the next best contact for each recipient.
      - Prior failed attempt with status: invalid contact.
    - If multiple people are messaging the same recipient via the same contact
      detail, the messages get combined into a single attempt.
      - Multiple mrs to same recipient.
    '''
    people_data = [
        dict(data=('Gerald Fnord', 'President', 'ocd-person/1'),
             contacts=(
                (ContactType.voice, '202-555-5555'),
                (ContactType.email, 'ger@facemail.com'),
                (ContactType.email, 'theprez@okcupid.com'),
                )
            ),
        dict(data=('Betty Fnord', 'Queen', 'ocd-person/2'),
             contacts=(
                (ContactType.voice, '202-555-5556'),
                (ContactType.sms, '202-555-5556'),
                (ContactType.email, 'theq@okcupid.com'),
                )
            ),
        dict(data=('Henry Fnord', 'CEO', 'ocd-person/2'),
             contacts=(
                (ContactType.voice, '202-555-5557'),
                (ContactType.email, 'hen@facemail.com'),
                (ContactType.email, 'bossman@okcupid.com'),
                )
            ),
        ]

    def tearDown(self):
        app.conf.ENGINE = self._old_engine

    def setUp(self):
        self._old_engine = app.conf.ENGINE
        app.conf.ENGINE = DumbSmartEngine()
        self.application = Application.objects.create(name='app', contact='fake@example.com',
                                                 template_set='')
        self.sender = Sender.objects.create(name='sender', email_expires_at=EXPIRY, id='1'*64)

        self.people = []
        for person_data in self.people_data:
            name, title, ocd_id = person_data['data']
            person = Person.objects.create(
                ocd_id=ocd_id,
                title=title,
                name=name)
            for contact_type, value in person_data['contacts']:
                contact = ContactDetail.objects.create(
                    person=person,
                    type=contact_type,
                    value=value)
                person.contacts.add(contact)
            self.people.append(person)

        app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
        app.conf.CELERY_ALWAYS_EAGER = True
        app.conf.BROKER_BACKEND = 'memory'

    def test_dont_send_untimely_followup(self):
        '''Make sure that a follow-up message get's dropped if the
        nag period hasn't elapsed.
        '''
        engine = DumbSmartEngine()

        # Create a successful delivery attempt from last week.
        msg = Message.objects.create(
            type=MessageType.private, sender=self.sender,
            subject='subject', message='hello everyone',
            application=self.application)
        mr = MessageRecipient.objects.create(
            recipient=self.people[0], message=msg)
        contact = engine.choose_contact(mr)

        diff = engine.nag_period - datetime.timedelta(days=1)
        earlier = datetime.datetime.utcnow() - diff
        earlier = earlier.replace(tzinfo=utc)
        attempt = DeliveryAttempt.objects.create(
            contact=contact,
            engine=engine.__class__.__name__,
            status=DeliveryStatus.success,
            created_at=earlier,
            updated_at=earlier)

        # Back-date this attempt.
        attempt.created_at = earlier
        attempt.updated_at = earlier
        attempt.messages.add(mr)
        attempt.save()

        # The attempts from before we call create_attempts.
        attempts_before = list(mr.attempts.all())

        # Now if we try to create a new delivery attempt with this
        # mr, it'll get dropped and no attempt will be created.
        engine.create_attempts([mr])

        # The attempts from after we call create_attempts.
        attempts_after = list(mr.attempts.all())

        self.assertEqual(attempts_before, attempts_after)

    @mock.patch('engine.engines.base.send_task')
    def test_send_timely_followup(self, send_task):
        '''If the nag period has elapsed, ensure that a successful but
        un-replied mr is allowed to create a follow-up message. Verify
        the follow-up uses a different contact method than the first,
        ignored message.
        '''
        engine = DumbSmartEngine()

        # Create a successful delivery attempt from last week.
        msg = Message.objects.create(
            type=MessageType.private, sender=self.sender,
            subject='subject', message='hello everyone',
            application=self.application)
        mr = MessageRecipient.objects.create(
            recipient=self.people[0], message=msg)
        contact = engine.choose_contact(mr)

        diff = engine.nag_period + datetime.timedelta(days=1)
        earlier = datetime.datetime.utcnow() - diff
        earlier = earlier.replace(tzinfo=utc)
        attempt = DeliveryAttempt.objects.create(
            contact=contact,
            engine=engine.__class__.__name__,
            status=DeliveryStatus.success)

        # Back-date this attempt.
        attempt.created_at = earlier
        attempt.updated_at = earlier
        attempt.messages.add(mr)
        attempt.save()

        # The attempts from before we call create_attempts.
        attempts_before = list(mr.attempts.all())

        # Now if we try to create a new delivery attempt with this
        # mr, it will be created for nagging purposes.
        engine.create_attempts([mr])

        # The attempts from after we call create_attempts.
        attempts_after = list(mr.attempts.order_by('created_at'))

        # This time, a new attempt to nag should have been created.
        self.assertEqual(1, len(attempts_before))
        self.assertEqual(2, len(attempts_after))

        first, second = attempts_after

        # And the subsequent nag attempt should have chosen a new
        # contact method.
        self.assertNotEqual(first.contact, second.contact)

        # Because Mr. Fnord has two email addresses, and
        # this particular engine defines email as the highest priority
        # contact type, the new contact method should be email.
        self.assertEqual('email', second.contact.type)

        # Ensure send_task was called with the new attempt.
        new_attempt = attempts_after.pop()
        process_func = 'engine.tasks.process_delivery_attempt'
        send_task.assert_called_once_with(process_func, args=(new_attempt,))

    @mock.patch('engine.engines.base.send_task')
    def test_skip_failed_contact(self, send_task):
        '''If mr has a prior failed delivery attempt, ensure the
        new attempt uses a different contact attempt.
        '''
        engine = DumbSmartEngine()

        # Create a successful delivery attempt from last week.
        msg = Message.objects.create(
            type=MessageType.private, sender=self.sender,
            subject='subject', message='hello everyone',
            application=self.application)
        betty = self.people[1]
        mr = MessageRecipient.objects.create(recipient=betty, message=msg)
        contact = engine.choose_contact(mr)

        diff = engine.nag_period + datetime.timedelta(days=1)
        earlier = datetime.datetime.utcnow() - diff
        earlier = earlier.replace(tzinfo=utc)
        attempt = DeliveryAttempt.objects.create(
            contact=contact,
            engine=engine.__class__.__name__,
            status=DeliveryStatus.invalid)

        # Back-date this attempt.
        attempt.created_at = earlier
        attempt.updated_at = earlier
        attempt.messages.add(mr)
        attempt.save()

        # The attempts from before we call create_attempts.
        attempts_before = list(mr.attempts.all())
        engine.create_attempts([mr])

        # The attempts from after we call create_attempts.
        attempts_after = list(mr.attempts.order_by('created_at'))

        # This time, a new attempt to nag should have been created.
        self.assertEqual(1, len(attempts_before))
        self.assertEqual(2, len(attempts_after))

        first, second = attempts_after

        # And the subsequent nag attempt should have chosen a new
        # contact method.
        self.assertNotEqual(first.contact, second.contact)

        # Because Betty Fnord only has email address, and
        # this particular engine defines voice as the second priority
        # contact type, the new contact method should be voice.
        self.assertEqual('voice', second.contact.type)

        # Ensure send_task was called with the new attempt.
        new_attempt = attempts_after.pop()
        process_func = 'engine.tasks.process_delivery_attempt'
        send_task.assert_called_once_with(process_func, args=(new_attempt,))

    # @mock.patch('engine.engines.base.send_task')
    # def test_groupby_recipient(self, send_task):
    #     '''If mr has a prior failed delivery attempt, ensure the
    #     new attempt uses a different contact attempt.
    #     '''
    #     engine = DumbSmartEngine()

    #     # Create 3 delivery attempts to Henry Fnord.
    #     mrs = []
    #     for i in range(3):
    #         msg = Message.objects.create(
    #             type=MessageType.private, sender=self.sender,
    #             subject='subject', message='hello everyone %d' % i,
    #             application=self.application)
    #         henry = self.people[2]
    #         mr = MessageRecipient.objects.create(recipient=henry, message=msg)
    #         mrs.append(mr)

    #     # The attempts from before we call create_attempts.
    #     attempts_before = list(mr.attempts.all())
    #     engine.create_attempts(mrs)

    #     # The attempts from after we call create_attempts.
    #     attempts_after = list(mr.attempts.order_by('created_at'))

    #     # This time, only 1 consolidated attempt should exist.
    #     self.assertEqual(0, len(attempts_before))
    #     self.assertEqual(1, len(attempts_after))

    #     attempt = attempts_after.pop(0)

    #     # And the single attempt should have 3 assoc'd messages.
    #     self.assertEqual(3, attempt.messages.count())

    #     # The contact method should be email.
    #     self.assertEqual('email', attempt.contact.type)

    #     # Ensure send_task was called with the new attempt.
    #     process_func = 'engine.tasks.process_delivery_attempt'
    #     send_task.assert_called_once_with(process_func, args=(attempt,))
