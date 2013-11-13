from django.db import models
from contact.models import DeliveryAttempt


class TwilioStatus(models.Model):
    attempt = models.ForeignKey(DeliveryAttempt, unique=True)
    remote_id = models.CharField(max_length=36)
