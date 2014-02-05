from django.views.decorators.http import require_http_methods
from django.contrib.sites.models import get_current_site
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from ..utils import body_template_to_string
from ..models import DeliveryStatus
from .models import TwilioVoiceStatus


@csrf_exempt
def call(request, contact_id):
    status = TwilioVoiceStatus.objects.get(id=contact_id)
    attempt = status.attempt
    template = attempt.template

    attempt.mark_attempted(
        DeliveryStatus.sent,
        'twilio_voice',
        attempt.template
    )

    return render(
        request,
        'plugins/{template}/voice.xml'.format(template=template),
        {
            "attempt": attempt,
            "status": status,
            "body": body_template_to_string(attempt.template, 'voice', attempt)
        },
        content_type="application/xml"
    )
