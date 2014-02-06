from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from ..base.twilio import validate

# from ..utils import body_template_to_string
# from contact.models import DeliveryStatus
from .models import TwilioSMSStatus


@csrf_exempt
@validate
def text(request, contact_id):
    status = TwilioSMSStatus.objects.get(id=contact_id)
    pass
