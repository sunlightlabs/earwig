from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from ..base.twilio import validate, normalize_number
from django.http import Http404

# from ..utils import body_template_to_string
from contact.models import FeedbackType
from .models import TwilioSMSStatus


def _handle_unsubscribe(request, number):

    status = TwilioSMSStatus.objects.filter(
        sent_to_normalized=normalize_number(number)
    )

    status = status[0] if status else None

    if status is None:
        raise Http404("No such number on record.")

    da = status.attempt
    da.set_feedback(
        FeedbackType.contact_detail_blacklist,
        "Text-based unsubscribe notification",
    )

    da.save()
    status.save()

    return render(request, "common/twilio/unsubscribe.xml", {
        "request": request,
        "from": number,
    }, content_type="application/xml")


def _handle_start(request, number):
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
    from_ = normalize_number(request.POST.get("From"))

    if from_ is None:
        raise Http404("No number")

    if body in MESSAGE_HANDLERS:
        return MESSAGE_HANDLERS[body](request, from_)

    return render(request, "common/twilio/inbound.xml", {
        "request": request,
        "body": body,
        "from": from_,
    }, content_type="application/xml")
