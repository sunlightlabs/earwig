import json
import time
import email
import datetime as dt

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import utc
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied

import pystmark

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
    # First, verify that this payload originated from postmark, not from
    # mischeivous teenagers forging flame messages to people in our system.
    allowed_hosts = [
        'testserver',  # The host during "manage.py test"
        settings.POSTMARK_INBOUND_HOST]

    if request.get_host() not in allowed_hosts:
        return PermissionDenied('Hey. You are not allowed.')

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

    # First, verify that this payload originated from postmark, not from
    # mischeivous teenagers forging flame messages to people in our system.
    allowed_hosts = [
        'testserver',  # The host during "manage.py test"
        settings.POSTMARK_INBOUND_HOST]

    if request.get_host() not in allowed_hosts:
        return PermissionDenied('Hey. You are not allowed.')

    mail = json.loads(request.read().decode('utf-8'))

    created_at = email.utils.parsedate(mail['Date'])
    created_at = dt.datetime.fromtimestamp(time.mktime(created_at))
    created_at = created_at.replace(tzinfo=utc)

    # Handle reply emails.
    if mail.get('MailboxHash'):
        reply = MessageReply.objects.create(
            body=mail['TextBody'],
            subject=mail['Subject'],
            email=mail['FromFull']['Email'],
            message_recip_id=int(mail['MailboxHash']),
            created_at=created_at)
        return HttpResponse()

    # Handle random, uninitiated emails.
    return handle_inbound_unsolicited(mail)


def handle_inbound_unsolicited(mail):
    '''Mail that arrives at this view was sent directly to cow@earwig.com
    without an id (like cow+12345@earwig.com). In response, we'll send a
    generic "Hi! What are you doing?" email.
    '''
    # Create the reply-to address.
    if settings.POSTMARK_MX_FORWARDING_ENABLED:
        inbound_host = settings.EARWIG_INBOUND_EMAIL_HOST
    else:
        inbound_host = settings.POSTMARK_INBOUND_HOST
    reply_to_tmpl = '{0.POSTMARK_INBOUND_HASH}@{1}'
    reply_to = reply_to_tmpl.format(settings, inbound_host)

    subject_tmpl = 'plugins/default/email/unsolicited/subject.txt'
    body_text_tmpl = 'plugins/default/email/unsolicited/body.txt'
    body_html_tmpl = 'plugins/default/email/unsolicited/body.html'

    message = pystmark.Message(
        sender=settings.EARWIG_EMAIL_SENDER,
        reply_to=reply_to,
        to=mail['FromFull']['Email'],
        subject=render_to_string(subject_tmpl, {}),
        text=render_to_string(body_text_tmpl, {}),
        html=render_to_string(body_html_tmpl, {}))
    pystmark.send(message, settings.POSTMARK_API_KEY)
    return HttpResponse()
