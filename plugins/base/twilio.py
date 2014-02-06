# Helper methods for the twilio plugins.
from django.conf import settings
from django.http import HttpResponse


def validate(fn):
    def _(request, *args, **kwargs):
        twilio_settings = settings.CONTACT_PLUGIN_TWILIO
        # Right. We're going to validate that the incoming twilio sid is
        # the one we have on file. This will help to avoid blatent
        # POSTs back at the URL.
        incoming_sid = request.POST['AccountSid']
        if incoming_sid != twilio_settings['account_sid']:
            return HttpResponse("Something went wrong.")
        return fn(request, *args, **kwargs)
    return _
