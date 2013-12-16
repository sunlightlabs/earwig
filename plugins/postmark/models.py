from django.db import models


class PostmarkDeliveryMeta(models.Model):
    attempt = models.ForeignKey('contact.DeliveryAttempt', unique=True)
    message_id = models.CharField(max_length=36)

    def __unicode__(self):
        return self.message_id
