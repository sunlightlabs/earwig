import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'earwig.settings.dev')

from datetime import timedelta
from celery import Celery
#from contact.models import ContactType
from engine.engines.dumb import DumbEngine
from engine.engines.dumbsmartengine import DumbSmartEngine

from plugins.twilio_sms.earwig import TwilioSmsContact
from plugins.twilio_voice.earwig import TwilioVoiceContact
from plugins.postmark.earwig import PostmarkPlugin

app = Celery('earwig', include=['engine.tasks'])
app.conf.CELERY_ENABLE_UTC = True
app.conf.CELERYBEAT_SCHEDULE = {
    'create-delivery-attempts': {
        'task': 'engine.tasks.create_delivery_attempts',
        'schedule': timedelta(seconds=5),
    },
    'janitor': {
        'task': 'engine.tasks.janitor',
        'schedule': timedelta(seconds=5),
    },
}

app.conf.EARWIG_PLUGINS = {
    "sms": TwilioSmsContact(),
    "voice": TwilioVoiceContact(),
    "email": PostmarkPlugin(),
}
app.conf.ENGINE = DumbSmartEngine()

if __name__ == '__main__':
    app.start()
