from django.dispatch import receiver
from django.db.models.signals import post_save

from contact.models import MessageReply


@receiver(post_save, sender=MessageReply)
def on_message_reply_save(sender, **kwargs):
    from engine.core import app
    plugin = app.conf.EARWIG_PLUGINS['email']
    plugin.send_reply_notification(kwargs['instance'])