import json
from datetime import datetime

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

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
    data = json.load(request)
    meta = PostmarkDeliveryMeta.objects.get(message_id=data['MessageID'])
    status = convert_bounce_to_delivery_status(data['Type'])
    meta.attempt.status = status
    meta.attempt.save()
    return HttpResponse()


@csrf_exempt
def handle_inbound(request):
    '''Body should be a json payload. See:
    http://developer.postmarkapp.com/developer-inbound-configure.html
    '''
    raise NotImplemented()
    return HttpResponse()
