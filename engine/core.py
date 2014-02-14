import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'earwig.settings.dev')

from datetime import timedelta
from celery import Celery
#from contact.models import ContactType
from engine.engines.dumb import DumbEngine
from engine.engines.newengine import NewEngine

app = Celery('earwig', include=['engine.tasks'])
app.conf.CELERY_ENABLE_UTC = True
app.conf.CELERYBEAT_SCHEDULE = {
    'create-delivery-attempts': {
        'task': 'engine.tasks.create_delivery_attempts',
        'schedule': timedelta(seconds=5),
    }
}

app.conf.EARWIG_PLUGINS = {
}
#app.conf.ENGINE = DumbEngine()
app.conf.ENGINE = NewEngine()

if __name__ == '__main__':
    app.start()
