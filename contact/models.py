import uuid
import hashlib
import six
from django.db import models
from django.core.urlresolvers import reverse
from django.conf import settings


class ChoiceEnumBase(type):
    # allow declarative assignment but attribute access

    def __new__(cls, name, bases, attrs):
        choices = []  # django choices
        valid_choices = set()  # set of choices for quick validation

        for key, attr in attrs.items():
            if not key.startswith('__'):
                choices.append((key, attr))
                attrs[key] = key

        obj = type.__new__(cls,  name, bases, attrs)
        obj.choices = choices
        return obj


@six.add_metaclass(ChoiceEnumBase)
class ChoiceEnum(object):
    pass


class ContactType(ChoiceEnum):
    """ each contact detail is of one of these types, and a plugin can handle a single type """
    voice = 'Voice Phone'
    sms = 'SMS'
    fax = 'Fax'
    email = 'Email'
    mail = 'Postal Address'
    twitter = 'Twitter'


class MessageType(ChoiceEnum):
    public = 'Public'
    private = 'Private'
    removed = 'Removed by Moderator'


class MessageStatus(ChoiceEnum):
    unscheduled = 'Unscheduled'
    pending = 'Pending'
    attempted = 'Attempted'         # attempt made, keep trying
    expired = 'Expired'             # we've tried and failed
    sent = 'Sent'                   # tried and succeeded


class DeliveryStatus(ChoiceEnum):
    scheduled = 'This is a scheduled delivery attempt.'

    sent = 'Sent successfully, pending further action'
    invalid = 'The contact information in question was invalid.'
    retry = 'The contact attempt can be safely retried without modification.'

    # statuses that can be set via a response
    bad_data = 'The contact information in question was for someone else.'
    blocked = 'Recipient requested no further contact.'
    success = 'This delivery attempt was successful.'


class FeedbackType(ChoiceEnum):
    none = 'None'
    offensive = 'Offensive'
    wrong_person = 'Wrong person'
    contact_detail_blacklist = 'Bad method'
    unsubscribe = 'Unsubscribe'


def _random_uuid():
    return uuid.uuid4().hex


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


class Person(models.Model):
    """ a person that can be contacted """
    ocd_id = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    photo_url = models.URLField()
    # more needed here from upstream

    def __str__(self):
        return self.name
    __unicode__ = __str__

    def get_attempts(self):
        """ Get all attempts to this person. More accurately,
        get all attempts to this person's contact details. """
        contact_ids = self.contacts.values_list('pk')
        return DeliveryAttempt.objects.filter(contact_id__in=contact_ids)


class ContactDetail(models.Model):
    """ contact details for a Person, popolo-like """
    person = models.ForeignKey(Person, related_name='contacts')
    type = models.CharField(max_length=10, choices=ContactType.choices)
    value = models.CharField(max_length=100)
    note = models.CharField(max_length=100)
    blacklisted = models.BooleanField(default=False)

    def __str__(self):
        return self.value
    __unicode__ = __str__


class Message(models.Model):
    """ a message to one or more people """
    id = models.CharField(max_length=32, default=_random_uuid, primary_key=True)
    type = models.CharField(max_length=10, choices=MessageType.choices)
    sender = models.ForeignKey(Sender, related_name='messages')
    application = models.ForeignKey(Application, related_name='messages')
    subject = models.CharField(max_length=100)
    message = models.TextField()
    recipients = models.ManyToManyField(Person, through='MessageRecipient')

    def __str__(self):
        return 'from %s' % self.sender.name
    __unicode__ = __str__


class MessageRecipient(models.Model):
    """ allows association of a status with a message & recipient """
    message = models.ForeignKey(Message)
    recipient = models.ForeignKey(Person, related_name='messages')
    status = models.CharField(max_length=10, choices=MessageStatus.choices,
                              default=MessageStatus.unscheduled)

    def __str__(self):
        return self.recipient.name
    __unicode__ = __str__


class DeliveryAttempt(models.Model):
    """ marks an attempted delivery of one or more messages """
    contact = models.ForeignKey(ContactDetail, related_name='attempts')
    messages = models.ManyToManyField(MessageRecipient, related_name='attempts')
    engine = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=DeliveryStatus.choices,
                              default=DeliveryStatus.scheduled)

    # plugin-set fields
    plugin = models.CharField(max_length=20)
    template = models.CharField(max_length=100)

    # feedback fields
    feedback_type = models.CharField(max_length=50, choices=FeedbackType.choices,
                                     default=FeedbackType.none)
    feedback_note = models.TextField()

    # timestamp fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'to {0} on {1}'.format(self.contact.person.name,
                                      self.created_at.strftime('%Y-%m-%d'))
    __unicode__ = __str__

    def unsubscribe_token(self):
        m = hashlib.md5()
        m.update(str(self.id).encode('ascii'))
        m.update(str(settings.SECRET_KEY).encode('ascii'))  # THIS IS CRITICAL TO GET RIGHT
        return m.hexdigest()

    def verify_token(self, token):
        return token == self.unsubscribe_token()

    def set_feedback(self, type_, note):
        self.feedback_type = type_
        self.feedback_note = note
        self.save()

    def mark_attempted(self, status, plugin, template):
        self.status = status
        self.plugin = plugin
        self.template = template
        self.save()

    @property
    def unsubscribe_url(self):
        return ''.join([settings.EARWIG_PUBLIC_LINK_ROOT,
                       reverse('flag', args=(str(self.id),
                                             str(self.unsubscribe_token())))])

    def is_first_via_contact_detail(self):
        """ Returns whether this is the first attempt to
        contact the recipient via this contact detail. """
        return bool(self.contact.attempts.count())

    def is_first_via_contact_medium(self):
        """ Returns whether this is the first attempt to
        contact the recipient via this contact detail. """
        attempts = self.contact.person.get_attempts()
        return attempts.filter(contact__type=self.contact.type)

    def is_first_for_recipient(self):
        """ Whether this is the first attempt to contact the
        recipient. """
        return bool(self.contact.person.get_attempts())


class MessageResponseStatisticTypes(ChoiceEnum):
    reply_good = 'It was a good reply'
    reply_bad = 'It was a bad reply'
    reply_none = 'I got no reply'
    reply_unknown = "I'm not sure if I got a reply"


class MessageResponseStatistic(models.Model):
    message_feedback = models.CharField(
        max_length=50,
        choices=MessageResponseStatisticTypes.choices,
        default=FeedbackType.none,
    )
    delivery_attempt = models.ForeignKey(DeliveryAttempt)


class MessageReply(models.Model):

    created_at = models.DateTimeField()
    from_original_sender = models.BooleanField()
    subject = models.CharField(max_length=100, null=True)
    message_recip = models.ForeignKey(MessageRecipient, related_name='replies')

    # This field arguably is insconsistent with Message.message
    body = models.TextField()

    @property
    def thread_id(self):
        return self.message_recip.id
