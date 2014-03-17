from django.db import models


class OrmDeliveryMeta(models.Model):
    attempt = models.ForeignKey('contact.DeliveryAttempt', unique=True)
