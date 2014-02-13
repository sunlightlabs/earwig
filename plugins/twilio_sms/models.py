from django.db import models
from contact.models import DeliveryAttempt


class TwilioSMSStatus(models.Model):
    attempt = models.ForeignKey(DeliveryAttempt, unique=True)
    sent_to = models.CharField(max_length=80)  # Phone number
    sent_to_normalized = models.CharField(max_length=80)  # Phone number
    sent_from = models.CharField(max_length=80)  # Phone number
    sent = models.BooleanField()

    objects = models.Manager()
