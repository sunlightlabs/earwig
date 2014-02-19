from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from ..base.twilio import validate

from ..utils import body_template_to_string
from contact.models import DeliveryStatus
from .models import TwilioVoiceStatus


def get_translate_contact(func):
    def get_translate_contact(request, contact_id, *args):
        status = TwilioVoiceStatus.objects.get(id=contact_id)
        return func(request, status, *args)
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

@csrf_exempt
@validate
@get_translate_contact
def intro(request, status):
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
        content_type="application/xml"
    )
