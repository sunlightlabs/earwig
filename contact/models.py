import uuid
import hashlib
import StringIO
import datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings

def _random_uuid():
    return uuid.uuid4().get_hex()


class Application(models.Model):
    """ a service that makes use of the contact API """
    name = models.CharField(max_length=200)
    contact = models.EmailField()
    key = models.CharField(max_length=32, default=_random_uuid)
    template_set = models.CharField(max_length=100)
    active = models.BooleanField(default=True)


class Sender(models.Model):
    """ a user that can send messages """
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_expires_at = models.DateTimeField()


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

    def __unicode__(self):
        return self.name


class ContactDetail(models.Model):
    """ contact details for a Person, popolo-like """
    person = models.ForeignKey(Person, related_name='contacts')
    type = models.CharField(max_length=10, choices=CONTACT_TYPES)
    value = models.CharField(max_length=100)
    note = models.CharField(max_length=100)
    blacklisted = models.BooleanField(default=False)

    def __unicode__(self):
        return self.value


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
    id = models.CharField(max_length=32, default=_random_uuid, primary_key=True)
    type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    sender = models.ForeignKey(Sender, related_name='messages')
    application = models.ForeignKey(Application, related_name='messages')
    subject = models.CharField(max_length=100)
    message = models.TextField()
    recipients = models.ManyToManyField(Person, through='MessageRecipient')

    def __unicode__(self):
        return 'from %s' % self.sender.name


class MessageRecipient(models.Model):
    """ allows association of a status with a message & recipient """
    message = models.ForeignKey(Message)
    recipient = models.ForeignKey(Person, related_name='messages')
    status = models.CharField(max_length=10, choices=MESSAGE_STATUSES)

    def __unicode__(self):
        return self.recipients[0].name


class DeliveryAttempt(models.Model):
    """ marks an attempted delivery of one or more messages """
    contact = models.ForeignKey(ContactDetail, related_name='attempts')
    messages = models.ManyToManyField(MessageRecipient, related_name='attempts')
    status = models.CharField(max_length=10, choices=DELIVERY_STATUSES, default='scheduled')
    date = models.DateTimeField()
    engine = models.CharField(max_length=20)

    def __unicode__(self):
        buf = StringIO.StringIO()
        buf.write('to %r ' % self.contact.person.name)
        buf.write('on %s' % self.date.strftime('%Y-%m-%d'))
        return buf.getvalue()

    def unsubscribe_token(self):
        m = hashlib.md5()
        m.update(str(self.id))
        m.update(settings.SECRET_KEY)  # THIS IS CRITICAL TO GET RIGHT
        return m.hexdigest()

    def verify_token(self, token):
        return token == self.unsubscribe_token()

    @property
    def unsubscribe_url(self):
        return "%s%s" % (settings.EARWIG_PUBLIC_LINK_ROOT,
                         reverse('flag', args=(
                             str(self.id), str(self.unsubscribe_token()))))



FEEDBACK_TYPES = (
    ('offensive', 'Offensive'),
    ('wrong-person', "Wrong person"),
    ('contact-detail-blacklist', "Bad method"),
    ('unsubscribe', 'Unsubscribe'),

    # Email/postmark types.
    ('vendor-unsubscribe', 'Vendor - Unsubscribe'),
    ('vendor-hard-bounce', 'Vendor - Hard bounce'),
    ('verndor-bounce', 'Vendor - Soft bounce'),
    ('verndor-autoresponder', 'Vendor - Autoresponder'),
    ('verndor-bad-email-address', 'Vendor - Bad email address'),
    ('verndor-spam-notification', 'Vendor - Spam Notification'),
    ('verndor-spam-complaint', 'Vendor - Spam Complaint'),
    ('verndor-blocked', 'Vendor - Blocked'),
)


class ReceiverFeedback(models.Model):
    """ Marks feedback from a user """
    attempt = models.ForeignKey(DeliveryAttempt, related_name='feedback',
                                unique=True)
    note = models.TextField()
    date = models.DateTimeField()
    feedback_type = models.CharField(max_length=64, choices=FEEDBACK_TYPES)  # Flag type.

    def __unicode__(self):
        return self.feedback_type