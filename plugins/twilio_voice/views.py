from .models import TwilioVoiceStatus
from django.shortcuts import render
from ..utils import body_template_to_string


def call(request, contact_id):
    status = TwilioVoiceStatus.objects.get(id=contact_id)
    attempt = status.attempt
    template = attempt.template

    return render(
        request,
        'plugins/{template}/voice.xml'.format(template=template),
        {
            "attempt": attempt,
            "status": status,
            "body": body_template_to_string(attempt.template, 'voice', attempt)
        },
        content_type="application/xhtml+xml"
    )
