import json
from datetime import datetime

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from plugins.postmark.models import PostmarkDeliveryMeta


@csrf_exempt
def handle_bounce(request):
    '''Body should be a json payload. See:
    http://developer.postmarkapp.com/developer-bounces.html#bounce-hooks
    {
      "ID" : [ID],
      "Type" : "HardBounce",
      "Tag" : "Invitation",
      "MessageID" : "d12c2f1c-60f3-4258-b163-d17052546ae4",
      "TypeCode" : 1,
      "Email" : "jim@test.com",
      "BouncedAt" : "2010-04-01",
      "Details" : "test bounce",
      "DumpAvailable" : true,
      "Inactive" : true,
      "CanActivate" : true,
      "Subject" : "Hello from our app!"
    }
    '''
    # See bounce types here:
    #   http://developer.postmarkapp.com/developer-bounces.html#bounce-hooks
    bounce_types = dict([
        ('HardBounce', None),
        ('Transient', None),
        ('Unsubscribe', 'unsubscribe'),
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
        ('BadEmailAddress', 'wrong-person'),
        ('SpamComplaint', 'unsubscribe'),
        ('ManuallyDeactivated', None),
        ('Unconfirmed', None),
        ('Blocked', 'contact-detail-blacklist'),
        ('SMTPApiError ', None),
        ('InboundError ', None),
    ])

    payload = request.read()
    data = json.loads(payload)
    meta = PostmarkDeliveryMeta.objects.get(message_id=data['MessageID'])
    attempt = meta.attempt

    # Certain bounce types indicate an invalid email address.
    INVALID_EMAIL_TYPES = ('HardBounce', 'BadEmailAddress',)
    if data['Type'] in INVALID_EMAIL_TYPES:
        attempt = meta.attempt
        attempt.status = 'invalid'
        attempt.save()

    # Others amount to receiver feedback.
    elif bounce_types.get(data['Type']):
        ReceiverFeedback.objects.create(attempt=meta.attempt,
                                        date=datetime.strptime(data['BouncedAt'], '%Y-%m-%d'),
                                        note=payload,
                                        feedback_type=bounce_types.get(data['Type']))

    # There are a few obscure ones that can just raise an error.
    else:
        msg = 'Weird postmark feedback type found: %r'
        raise ValueError(msg % data['Type'])

    return HttpResponse()


@csrf_exempt
def handle_inbound(request):
    '''Body should be a json payload. See:
    http://developer.postmarkapp.com/developer-inbound-configure.html
    '''
    raise NotImplemented()
    return HttpResponse()
