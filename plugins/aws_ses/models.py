from django.db import models


class SESDeliveryMeta(models.Model):
    attempt = models.ForeignKey('contact.models.DeliveryAttempt', unique=True)
    request_id = models.CharField(max_length=36)
    message_id = models.CharField(max_length=36)
