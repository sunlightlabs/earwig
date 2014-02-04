from celery import Celery
from datetime import timedelta

app = Celery('earwig', broker='django://', backend='django://', include=['engine.tasks'])
app.conf.CELERY_ENABLE_UTC = True
app.conf.CELERYBEAT_SCHEDULE = {
    'create-delivery-attempts': {
        'task': 'tasks.create_delivery_attempts',
        'schedule': timedelta(minutes=5),
    }
}

app.conf.EARWIG_PLUGINS = {
    #ContactType.voice: 
    ContactType.email: PostmarkContact,
}

if __name__ == '__main__':
    app.start()
