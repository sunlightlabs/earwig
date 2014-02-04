from .models import TwilioVoiceStatus
from django.shortcuts import render


def call(request, contact_id):
    da = TwilioVoiceStatus.objects.get(id=contact_id)
    template = da.attempt.template

    return render(
        request,
        'plugins/{template}/voice.xml'.format(template=template),
        {"attempt": da},
        content_type="application/xhtml+xml"
    )
