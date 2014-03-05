import json
import time
import email
import datetime as dt

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import utc

from contact.models import MessageReply
from plugins.postmark.earwig import PostmarkContact
from plugins.postmark.models import (
    PostmarkDeliveryMeta,
    convert_bounce_to_delivery_status)


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
    data = json.loads(request.body.decode('utf8'))
    meta = PostmarkDeliveryMeta.objects.get(message_id=data['MessageID'])
    status = convert_bounce_to_delivery_status(data['Type'])
    meta.attempt.status = status
    meta.attempt.save()
    return HttpResponse()


@csrf_exempt
def handle_inbound(request):
    '''Body should be a json payload. See:
    http://developer.postmarkapp.com/developer-inbound-configure.html

    document format:

    http://developer.postmarkapp.com/developer-inbound-parse.html
    mail = {
        "From": "myUser@theirDomain.com",
        "FromFull": {
            "Email": "myUser@theirDomain.com",
            "Name": "John Doe"
        },
        "To": "451d9b70cf9364d23ff6f9d51d870251569e+ahoy@inbound.postmarkapp.com",
        "ToFull": [{
            "Email": "451d9b70cf9364d23ff6f9d51d870251569e+ahoy@inbound.postmarkapp.com",
            "Name": ""}],
        ],
        "ReplyTo": "myUsersReplyAddress@theirDomain.com",
        "Subject": "This is an inbound message",
        "MessageID": "22c74902-a0c1-4511-804f2-341342852c90",
        "Date": "Thu, 5 Apr 2012 16:59:01 +0200",
        "MailboxHash": "ahoy",
        "TextBody": "[ASCII]",
        "HtmlBody": "[HTML(encoded)]",
        "Tag": "",
        "Headers": [{
            "Name": "X-Spam-Checker-Version",
            "Value": "SpamAssassin 3.3.1 (2010-03-16) onrs-ord-pm-inbound1.wildbit.com"
            },
        }
    '''
    mail = json.load(request)

    created_at = email.utils.parsedate(mail['Date'])
    created_at = dt.datetime.fromtimestamp(time.mktime(created_at))
    created_at = created_at.replace(tzinfo=utc)

    reply = MessageReply.objects.create(
        body=mail['TextBody'],
        subject=mail['Subject'],
        email=mail['FromFull']['Email'],
        message_recip_id=int(mail['MailboxHash']),
        created_at=created_at)
    return HttpResponse()
