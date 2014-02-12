# Helper methods for the twilio plugins.
from django.conf import settings
from django.http import Http404


def normalize_number(number):
    if number is None:
        return None

    number = number.replace(" ", "")
    number = number.replace(".", "")
    number = number.replace("(", "")
    number = number.replace(")", "")
    number = number.replace("-", "")
    number = number.replace("+", "")
    number = number[-10:]
    return number


def validate(fn):
    """
    Validate incoming Django requests that we expect a twilio callback against.
    This is to be used to decorate Django views.
    """

    def _(request, *args, **kwargs):
        twilio_settings = settings.CONTACT_PLUGIN_TWILIO
        # Right. We're going to validate that the incoming twilio sid is
        # the one we have on file. This will help to avoid blatent
        # POSTs back at the URL.
        incoming_sid = request.POST.get('AccountSid', None)

        # incoming_sid.startswith("AC")
        # incoming_sid length is 32
        # (We should add this if we start being more liberal with AccountSid
        #  that we get)

        if incoming_sid != twilio_settings['account_sid']:
            raise Http404("Something went wrong.")
        return fn(request, *args, **kwargs)
    return _
