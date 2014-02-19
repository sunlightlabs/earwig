from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from ..base.twilio import validate

from ..utils import body_template_to_string
from contact.models import DeliveryStatus
from .models import TwilioVoiceStatus


@csrf_exempt
@validate
def call(request, contact_id):
    status = TwilioVoiceStatus.objects.get(attempt__id=contact_id)
    attempt = status.attempt
    template = attempt.template

    attempt.mark_attempted(
        DeliveryStatus.sent,
        'twilio_voice',
        attempt.template
    )
    attempt.save()

    return render(
        request,
        'plugins/{template}/voice.xml'.format(template=template),
        {"attempt": attempt,
         "status": status,
         "body": body_template_to_string(attempt.template, 'voice', attempt)},
        content_type="application/xml"
    )
