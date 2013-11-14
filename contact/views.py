from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest, HttpResponse
from .models import Sender, Person, Message, MessageRecipient


@require_POST
def create_message(request):
    try:
        msg_type = request.POST['type']
        subject = request.POST['subject']
        message = request.POST['message']
        sender_uid = request.POST['sender']
    except KeyError as e:
        return HttpResponseBadRequest('missing parameter: {0}'.format(e))

    # look up sender
    try:
        sender = Sender.objects.get(pk=sender_uid)
    except Sender.DoesNotExist:
        return HttpResponseBadRequest('invalid sender')

    # add recipients by ocd_id
    recipients = []
    for recip_id in request.POST.getlist('recipients'):
        try:
            recipients.append(Person.objects.get(ocd_id=recip_id))
        except Person.DoesNotExist:
            return HttpResponseBadRequest('invalid recipient: {0}'.format(recip_id))

    # create message and recipient objects
    msg = Message.objects.create(type=msg_type, sender=sender, subject=subject, message=message)
    for recip in recipients:
        MessageRecipient.objects.create(message=msg, recipient=recip, status='pending')

    return HttpResponse(msg.id)
