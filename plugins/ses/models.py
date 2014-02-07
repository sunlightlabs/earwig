from django.db import models


class SESDeliveryMeta(models.Model):
    attempt = models.ForeignKey('contact.DeliveryAttempt', unique=True)
    message_id = models.CharField(max_length=36)