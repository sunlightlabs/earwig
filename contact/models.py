from django.db import models
from django.contrib.auth.models import User


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
    """ a user (anonymous or not) that can send messages """
    user = models.OneToOneField(User, null=True)
    verified = models.BooleanField(default=False)
    # tie to a session id?

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
    message = models.ForeignKey(Message, related_name='recipients')
    recipient = models.ForeignKey(Person, related_name='messages')
    status = models.CharField(max_length=10, choices=MESSAGE_STATUSES)


class DeliveryAttempt(models.Model):
    """ marks an attempted delivery of one or more messages """
    contact = models.ForeignKey(ContactDetail, related_name='attempts')
    messages = models.ManyToManyField(MessageRecipient, related_name='attempts')
    status = models.CharField(max_length=10, choices=DELIVERY_STATUSES, default='scheduled')
    date = models.DateTimeField()
    engine = models.CharField(max_length=20)
