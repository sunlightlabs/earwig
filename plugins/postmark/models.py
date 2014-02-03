from django.db import models


class PostmarkDeliveryMeta(models.Model):
    attempt = models.ForeignKey('contact.DeliveryAttempt', unique=True)
    message_id = models.CharField(max_length=36)

    def __unicode__(self):
        return self.message_id


def convert_bounce_to_delivery_status(bounce_type):
    '''Given a bounce type returned by the Postmark API, convert
    it to an earwig status.
    '''
    # See bounce types here:
    #   http://developer.postmarkapp.com/developer-bounces.html#bounce-hooks
    BOUNCE_TYPES = dict([
        ('HardBounce', None),
        ('Transient', None),
        ('Unsubscribe', 'blocked'),
        ('Subscribe', None),
        ('AutoResponder', None),
        ('AddressChange', None),
        ('DnsError ', None),
        ('SpamNotification ', None),
        ('OpenRelayTest', None),
        ('Unknown', None),
        ('SoftBounce ', None),
        ('VirusNotification', None),
        ('ChallengeVerification', None),
        ('BadEmailAddress', 'bad-data'),
        ('SpamComplaint', 'blocked'),
        ('ManuallyDeactivated', None),
        ('Unconfirmed', None),
        ('Blocked', 'blocked'),
        ('SMTPApiError ', None),
        ('InboundError ', None),
    ])

    # Certain bounce types indicate an invalid email address.
    INVALID_EMAIL_BOUNCE_TYPES = ('HardBounce', 'BadEmailAddress',)
    if bounce_type in INVALID_EMAIL_BOUNCE_TYPES:
        return 'invalid'

    # Others amount to receiver feedback.
    elif BOUNCE_TYPES.get(bounce_type):
        return BOUNCE_TYPES.get(bounce_type)

    # There are a few obscure ones that can just raise an error.
    else:
        msg = 'Weird postmark bounce type found: %r. '
        raise ValueError(msg % bounce_type)
