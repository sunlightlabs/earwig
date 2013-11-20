from django.conf import settings
from django.utils.timezone import utc
from django.views.decorators.http import require_GET, require_POST
from django.http import (HttpResponseBadRequest, HttpResponse,
                         HttpResponseNotFound)

from .models import Sender, Person, Message, MessageRecipient

import re
import json
import hashlib
import datetime



def _msg_to_json(msg):
    data = {'type': msg.type, 'sender': msg.sender_id, 'subject': msg.subject,
            'message': msg.message, 'recipients': []}
    for recip in MessageRecipient.objects.filter(message=msg):
        data['recipients'].append({'recipient_id': recip.recipient_id, 'status': recip.status})

    return json.dumps(data)

def _sender_to_json(sender):
    data = {'id': sender.id, 'name': sender.name, 'email': sender.email,
            'created_at': sender.created_at.isoformat(),
            'email_expires_at': sender.email_expires_at.isoformat()}
    return json.dumps(data)

def _get_or_create_sender(email, name, ttl):
    uid = hashlib.sha256(email + settings.EARWIG_SENDER_SALT).hexdigest()
    # ttl has to be at least one day
    ttl = max(1, ttl)
    expiry = datetime.datetime.utcnow().replace(tzinfo=utc) + datetime.timedelta(days=ttl)
    try:
        # look up sender and possibly update
        sender = Sender.objects.get(pk=uid)
        updated = False
        if sender.email != email:
            sender.email = email
            updated = True
        if sender.name != name:
            sender.name = name
            updated = True
        if expiry > sender.email_expires_at:
            sender.email_expires_at = expiry
            updated = True
        if updated:
            sender.save()
    except Sender.DoesNotExist:
        # create a new sender if uid hasn't been seen before
        sender = Sender.objects.create(id=uid, email=email, name=name,
                                       email_expires_at=datetime.datetime.utcnow())
    return sender


@require_POST
def create_sender(request):
    try:
        email = request.POST['email']
        name = request.POST['name']
        ttl = int(request.POST['ttl'])
    except KeyError as e:
        return HttpResponseBadRequest('missing parameter: {0}'.format(e))
    sender = _get_or_create_sender(email, name, ttl)
    return HttpResponse(_sender_to_json(sender))


@require_POST
def create_message(request):
    try:
        msg_type = request.POST['type']
        subject = request.POST['subject']
        message = request.POST['message']
        sender_payload = request.POST['sender']
    except KeyError as e:
        return HttpResponseBadRequest('missing parameter: {0}'.format(e))

    if re.match('[0-9a-f]{64}', sender_payload):
        # look up sender if it is a sha256
        try:
            sender = Sender.objects.get(pk=sender_payload)
        except Sender.DoesNotExist:
            return HttpResponseBadRequest('invalid sender')
    else:
        # otherwise it is a json payload
        # {'email': 'j@t.com', 'name': 'j', 'ttl': 4}
        sender_data = json.loads(sender_payload)
        try:
            sender = _get_or_create_sender(sender_data['email'], sender_data['name'],
                                           sender_data['ttl'])
        except KeyError as e:
            return HttpResponseBadRequest('sender payload missing field: {0}'.format(e))

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

    return HttpResponse(_msg_to_json(msg))


@require_GET
def get_message(request, message_id):
    try:
        msg = Message.objects.get(pk=message_id)
        return HttpResponse(_msg_to_json(msg))
    except Message.DoesNotExist:
        return HttpResponseNotFound('no such object')


# The following are public-use endpoints to allow for one-click
# unsubscribe, etc.
def unsubscribe(request, transaction, secret):
    print secret
    return HttpResponseNotFound('no such object')
