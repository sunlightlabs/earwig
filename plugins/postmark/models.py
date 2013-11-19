from django.db import models


class PostmarkEmailStatus(models.Model):
    attempt = models.ForeignKey('contact.models.DeliveryAttempt', unique=True)
    message_id = models.CharField(max_length=36)
