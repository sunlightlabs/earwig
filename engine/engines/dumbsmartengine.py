import datetime
from collections import defaultdict
from itertools import chain

from django.utils.timezone import utc

from contact.models import ContactType, DeliveryStatus, DeliveryAttempt
from plugins.postmark.earwig import PostmarkPlugin
from plugins.twilio_voice.earwig import TwilioVoiceContact
from plugins.twilio_sms.earwig import TwilioSmsContact
from .base import Engine


class DumbSmartEngine(Engine):
    '''This engine is basically an excercise in creating an engine
    that makes some decisions about grouping mrs together into a single
    attempt, falling back to alternative contact methods, and deciding
    whether it's time to allow a follow-up to a successful delivery
    or wait longer. It isn't meant to lock us into to the implementation,
    just to flesh out some common functions, and write some meaty tests.
    '''
    nag_period = datetime.timedelta(weeks=2)

    contact_priority = (
        ContactType.email,
        ContactType.voice,
        ContactType.sms,
        ContactType.twitter,
        ContactType.fax,
        ContactType.mail)

    def create_attempts(self, mrs):
        # Drop untimely followups.
        mrs = list(self.drop_mrs(mrs))

        # for recipient, mrs in self.groupby_recipient(mrs).items():
            # for contact, mrs in self.groupby_contact(mrs).items():
            #     self.create_attempt(contact, mrs)
        for mr in mrs:
            contact = self.choose_contact(mr)
            self.create_attempt(contact, [mr])

    # -----------------------------------------------------------------------
    # Functions for choosing next best available contact method.
    # -----------------------------------------------------------------------
    def get_failed_contacts(self, mr):
        '''Examine failed attempts and group their
        contact methods by DeliveryStatus.
        '''
        failed_status = (
            DeliveryStatus.bad_data,
            DeliveryStatus.invalid,
            DeliveryStatus.bad_data,
            DeliveryStatus.blocked)
        methods = defaultdict(list)
        for attempt in mr.attempts.all():
            if attempt.status in failed_status:
                methods[attempt.status].append(attempt.contact)
        return methods

    def get_succeeded_contacts(self, mr):
        successes = mr.attempts.filter(status=DeliveryStatus.success)
        return [attempt.contact for attempt in successes]

    def get_available_contacts(self, mr):
        return list(mr.recipient.contacts.all())

    def contact_method_sorter(self, contact):
        try:
            return self.contact_priority.index(contact.type)
        except ValueError:
            return None

    def choose_contact(self, mr):
        failed_contacts = self.get_failed_contacts(mr)
        available_contacts = self.get_available_contacts(mr)

        # Remove previously failed methods from avialables.
        for contact in chain.from_iterable(failed_contacts.values()):
            available_contacts.remove(contact)

        # Remove previously successful methods from availables if
        # recipient has not replied.
        if not self.recipient_has_replied(mr):
            for contact in self.get_succeeded_contacts(mr):
                available_contacts.remove(contact)

        if not available_contacts:
            raise ValueError('No contact methods available.')

        # Sort by class-level priority list.
        available_contacts.sort(key=self.contact_method_sorter)

        # Return best available method.
        return available_contacts.pop(0)

    # -----------------------------------------------------------------------
    # Functions for choosing whether to desliver or wait longer.
    # -----------------------------------------------------------------------
    def drop_mrs(self, mrs):
        '''Drop mrs with prior successfull attempts if the nag_period
        hasn't elapsed yet.
        '''
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        for mr in mrs:
            succeeded = mr.attempts.filter(status=DeliveryStatus.success)
            if not succeeded.count():
                yield mr
            else:
                recent_success = succeeded.order_by('updated_at').get()
                elapsed_time = now - recent_success.created_at
                reply_recieved = self.recipient_has_replied(mr)
                if (self.nag_period <= elapsed_time) and not reply_recieved:
                    yield mr

    def recipient_has_replied(self, mr):
        '''Assume no reply for now.
        '''
        return False

    # ----------------------------------------------------------------------
    # Functions for grouping mrs by various criteria.
    # -----------------------------------------------------------------------
    def groupby_contact(self, mrs):
        grouped = defaultdict(list)
        for mr in mrs:
            contact = self.choose_contact(mr)
            grouped[contact].append(mr)
        return grouped

    def groupby_recipient(self, mrs):
        grouped = defaultdict(list)
        for mr in mrs:
            grouped[mr.recipient].append(mr)
        return grouped

