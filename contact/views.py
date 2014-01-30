from django.views.decorators.http import require_GET, require_POST
from django.http import (HttpResponseBadRequest, HttpResponse,
                         HttpResponseNotFound)
from django.shortcuts import render
from django.utils.timezone import utc
from django.conf import settings

from .forms import FlaggingForm
from .models import Application, Sender, Person, Message, MessageRecipient, DeliveryAttempt

import re
import json
import hashlib
import datetime


def _msg_to_json(msg):
    """ util function for returning an entire message as JSON """
    data = {'type': msg.type, 'sender': msg.sender_id, 'subject': msg.subject,
            'message': msg.message, 'recipients': []}
    for recip in MessageRecipient.objects.filter(message=msg):
        data['recipients'].append({'recipient_id': recip.recipient_id, 'status': recip.status})

    return json.dumps(data)


def _sender_to_json(sender):
    """ util function for returning sender as JSON """
    data = {'id': sender.id, 'name': sender.name, 'email': sender.email,
            'created_at': sender.created_at.isoformat(),
            'email_expires_at': sender.email_expires_at.isoformat()}
    return json.dumps(data)


def _get_or_create_sender(email, name, ttl):
    """ either lookup or create a sender, optionally updating it """
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
        sender = Sender.objects.create(id=uid, email=email, name=name, email_expires_at=expiry)
    return sender


@require_POST
def create_sender(request):
    """ create a new sender (can also be done from within create_message call) """
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
    """ create a new message """
    # validate parameters
    try:
        msg_type = request.POST['type']
        subject = request.POST['subject']
        message = request.POST['message']
        sender_payload = request.POST['sender']
        app_key = request.POST['key']
    except KeyError as e:
        return HttpResponseBadRequest('missing parameter: {0}'.format(e))

    try:
        app = Application.objects.get(key=app_key)
    except Application.DoesNotExist:
        return HttpResponseBadRequest('invalid application key')

    # either get sender from database or construct one from a sender payload
    if re.match('[0-9a-f]{64}', sender_payload):
        # look up sender if it is a sha256
        try:
            sender = Sender.objects.get(pk=sender_payload)
        except Sender.DoesNotExist:
            return HttpResponseBadRequest('invalid sender')
    else:
        # otherwise it is a json payload
        # {'email': 'j@t.com', 'name': 'j', 'ttl': 4}
        try:
            sender_data = json.loads(sender_payload)
            sender = _get_or_create_sender(sender_data['email'], sender_data['name'],
                                           sender_data['ttl'])
        except KeyError as e:
            return HttpResponseBadRequest('sender payload missing field: {0}'.format(e))
        except ValueError:
            return HttpResponseBadRequest('invalid JSON')

    # add recipients by ocd_id
    recipients = []
    for recip_id in request.POST.getlist('recipients'):
        try:
            recipients.append(Person.objects.get(ocd_id=recip_id))
        except Person.DoesNotExist:
            return HttpResponseBadRequest('invalid recipient: {0}'.format(recip_id))

    # create message and recipient objects
    msg = Message.objects.create(type=msg_type, sender=sender, application=app, subject=subject,
                                 message=message)
    for recip in recipients:
        MessageRecipient.objects.create(message=msg, recipient=recip, status='pending')

    # return the complete message object
    return HttpResponse(_msg_to_json(msg))


@require_GET
def get_message(request, message_id):
    """ simply get a message if it exists """
    try:
        msg = Message.objects.get(pk=message_id)
        return HttpResponse(_msg_to_json(msg))
    except Message.DoesNotExist:
        return HttpResponseNotFound('no such object')


def flag(request, transaction, secret):
    """
    Create feedback on a DeliveryAttempt

    Templates:
        contact/flag-error.html
        contact/flag.html
        contact/flagged.html
    """
    # ensure we're dealing with a valid transaction
    invalid_reason = None
    try:
        attempt = DeliveryAttempt.objects.get(id=int(transaction))
        if not attempt.verify_token(secret):
            invalid_reason = 'invalid secret'
    except DeliveryAttempt.DoesNotExist:
        invalid_reason = 'no such attempt'

    # if there is already feedback on this attempt, that's an error too
    if attempt.feedback_type:
        invalid_reason = 'already flagged'

    # bail if there was an invalid reason
    if invalid_reason:
        return render(request, 'contact/flag-error.html', {'attempt': attempt,
                                                           'reason': invalid_reason},
                      status=400)

    # at this point we know we have a valid attempt & secret
    if request.method == 'POST':
        form = FlaggingForm(request.POST)
        if form.is_valid():
            attempt.set_feedback(form.cleaned_data['feedback_type'], form.cleaned_data['note'])

            return render(request, 'contact/flagged.html', {
                'form': form,
                "attempt": attempt,
            })

    form = FlaggingForm()

    return render(request, 'contact/flag.html', {
        'form': form,
        'attempt': attempt,
        'token': secret,
    })
