import hashlib

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings


CONTACT_TYPES = (
    ('voice', 'Voice Phone'),
    ('sms', 'SMS'),
    ('fax', 'Fax'),
    ('email', 'Email'),
    ('mail', 'Postal Address'),
    ('twitter', 'Twitter'),
)


class Person(models.Model):
    """ a person that can be contacted """
    ocd_id = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    photo_url = models.URLField()
    # more needed here from upstream


class ContactDetail(models.Model):
    """ contact details for a Person, popolo-like """
    person = models.ForeignKey(Person, related_name='contacts')
    type = models.CharField(max_length=10, choices=CONTACT_TYPES)
    value = models.CharField(max_length=100)
    note = models.CharField(max_length=100)
    blacklisted = models.BooleanField(default=False)


class Sender(models.Model):
    """ a user that can send messages """
    id = models.CharField(max_length=36, primary_key=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    email_expires_at = models.DateTimeField()


MESSAGE_TYPES = (
    ('public', 'Public'),
    ('private', 'Private'),
    ('removed', 'Removed by Moderator'),
)

MESSAGE_STATUSES = (
    ('pending', 'Pending'),         # not yet attempted
    ('attempted', 'Attempted'),     # attempts made, we'll keep trying
    ('expired', 'Expired'),         # we've tried, and failed
    ('received', 'Received'),       # we've tried, and there was success
)

DELIVERY_STATUSES = (
    # initial status
    ('scheduled', 'This is a scheduled delivery attempt.'),

    # possible statuses after attempt
    ('sent', 'Sent successfully, pending further action.'),
    ('invalid', 'The contact information in question was invalid.'),
    ('retry', 'The contact attempt can be safely retried without modification.'),

    # statuses that can be set via a response
    ('bad-data', 'The contact information in question was for someone else.'),
    ('blocked', 'Recipient requested no further contact.'),
    ('success', 'This delivery attempt was successful.'),
)


class Message(models.Model):
    """ a message to one or more people """
    type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    sender = models.ForeignKey(Sender, related_name='messages')
    subject = models.CharField(max_length=100)
    message = models.TextField()
    recipients = models.ManyToManyField(Person, through='MessageRecipient')


class MessageRecipient(models.Model):
    """ allows association of a status with a message & recipient """
    message = models.ForeignKey(Message)
    recipient = models.ForeignKey(Person, related_name='messages')
    status = models.CharField(max_length=10, choices=MESSAGE_STATUSES)


class DeliveryAttempt(models.Model):
    """ marks an attempted delivery of one or more messages """
    contact = models.ForeignKey(ContactDetail, related_name='attempts')
    messages = models.ManyToManyField(MessageRecipient, related_name='attempts')
    status = models.CharField(max_length=10, choices=DELIVERY_STATUSES, default='scheduled')
    date = models.DateTimeField()
    engine = models.CharField(max_length=20)

    def _unsubscribe_token(self):
        m = hashlib.md5()
        m.update(self.id)
        m.update(settings.SECRET_KEY)  # THIS IS CRITICAL TO GET RIGHT
        return m.hexdigest()

    @property
    def unsubscribe_url(self):
        r = reverse('unsubscribe', args=(
            str(self.id), str(self._unsubscribe_token())))
