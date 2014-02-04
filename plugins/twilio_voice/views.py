from .models import TwilioVoiceStatus
from django.shortcuts import render
from ..utils import body_template_to_string,


def call(request, contact_id):
    da = TwilioVoiceStatus.objects.get(id=contact_id)
    template = da.attempt.template

    return render(
        request,
        'plugins/{template}/voice.xml'.format(template=template),
        {
            "attempt": da,
            "body": body_template_to_string(attempt.template, 'voice', da)
        },
        content_type="application/xhtml+xml"
    )
