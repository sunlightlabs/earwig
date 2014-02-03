from celery import Celery

app = Celery('earwig', broker='django://', backend='django://', include=['engine.tasks'])

if __name__ == '__main__':
    app.start()
