from django.db import models
from contact.models import DeliveryAttempt


class SendgridDeliveryMeta(models.Model):
    attempt = models.ForeignKey(DeliveryAttempt, unique=True)
    # request_id = models.CharField(max_length=36)
    # message_id = models.CharField(max_length=36)
