from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from ..base.twilio import validate
from django.http import Http404

# from ..utils import body_template_to_string
# from contact.models import DeliveryStatus
from .models import TwilioSMSStatus


def _normalize_number(number):
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


def _handle_unsubscribe(request, number):
    return render(request, "common/twilio/unsubscribe.xml", {
        "request": request,
        "from": number,
    }, content_type="application/xml")


def _handle_unblacklist(request, number):
    return render(request, "common/twilio/start.xml", {
        "request": request,
        "from": number,
    }, content_type="application/xml")


MESSAGE_HANDLERS = {
    "unsubscribe": _handle_unsubscribe,
    "start": _handle_start,
}


@csrf_exempt
@validate
def text(request):
    body = request.POST.get("Body", "").lower().strip()
    from_ = _normalize_number(request.POST.get("From"))

    if from_ is None:
        raise Http404("No number")

    if body in MESSAGE_HANDLERS:
        return MESSAGE_HANDLERS[body](request, from_)

    return render(request, "common/twilio/inbound.xml", {
        "request": request,
        "body": body,
        "from": from_,
    }, content_type="application/xml")
