from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from ..base.twilio import validate

from ..utils import (intro_template_to_string, body_template_to_string,
                     subject_template_to_string)

from contact.models import DeliveryStatus
from .models import TwilioVoiceStatus


def get_translate_contact(func):
    def get_translate_contact(request, contact_id, *args, **kwargs):
        status = TwilioVoiceStatus.objects.get(attempt__id=contact_id)
        return func(request, status, *args, **kwargs)
    return get_translate_contact



#@csrf_exempt
#@validate
#@get_translate_contact
#def call(request, status):
#    attempt = status.attempt
#    template = attempt.template
#
#    attempt.mark_attempted(DeliveryStatus.sent,
#                           'twilio_voice', attempt.template)
#    attempt.save()
#
#    return render(request,
#                  'plugins/{template}/voice.xml'.format(template=template),
#                  {"attempt": attempt, "status": status,
#                   "body": body_template_to_string(
#                       attempt.template, 'voice', attempt)},
#                  content_type="application/xml")


def _redirect_to_messages(request, status):
    return render(request, 'common/twilio/voice/redirect.xml',
                  {"url": "../../messages/%s/" % (status.attempt.id)},
                  content_type="application/xml")


@csrf_exempt
#@validate
@get_translate_contact
def intro(request, status):
    digits = request.POST.get("Digits", None)
    if digits:
        try:
            return {
                "1": _redirect_to_messages,
            }[digits](request, status)
        except KeyError:
            # Random keypress.
            pass

    attempt = status.attempt
    template = attempt.template
    attempt.mark_attempted(DeliveryStatus.sent,
                           'twilio_voice', attempt.template)
    attempt.save()

    return render(request,
                  'common/twilio/voice/intro.xml',
                  {"attempt": attempt,
                   "status": status,
                   "intro": intro_template_to_string(attempt.template,
                                                     'voice.human',
                                                     attempt)},
                 content_type="application/xml")


@csrf_exempt
#@validate
@get_translate_contact
def messages(request, status):
    attempt = status.attempt
    template = attempt.template
    return render(request,
                  'common/twilio/voice/messages.xml',
                  {"attempt": attempt,},
                 content_type="application/xml")


@csrf_exempt
#@validate
@get_translate_contact
def message(request, status, sequence_id):
    digits = request.POST.get("Digits", None)
    # 1 => next
    # 3 => respond
    # 0 => main menu

    attempt = status.attempt
    template = attempt.template
    sequence_id = int(sequence_id)

    messages = list(attempt.messages.order_by('id'))
    message = messages[sequence_id].message
    print(message.message)
    has_next = len(messages) > (sequence_id + 1)

    return render(request,
                  'common/twilio/voice/message.xml',
                  {"attempt": attempt,
                   "has_next": has_next,
                   "message": message},
                 content_type="application/xml")
