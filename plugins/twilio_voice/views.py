from .models import TwilioVoiceStatus


def call(request, contact_id):
    da = TwilioVoiceStatus.objects.get(id=contact_id)
    print(da)
