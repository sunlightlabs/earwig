from datetime import datetime

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from contact.models import Message, DeliveryAttempt, ReceiverFeedback


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
    meta = PostmarkDeliveryMeta.objects.get(message_id=data['MessageID'])
    ReceiverFeedback.objects.create(
      attempt=meta.attempt,
      date=datetime.strptime(message['BouncedAt'], '%Y-%m-%d'),
      note=payload,
      feedback_type='unsubscribe')
    return HttpResponse()


@csrf_exempt
def handle_inbound(request):
    '''Body should be a json payload. See:
    http://developer.postmarkapp.com/developer-inbound-configure.html
    '''
    return HttpResponse()
