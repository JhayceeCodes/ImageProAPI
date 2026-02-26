import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'delete-expired-images-every-5-min': {
        'task': 'image_pro.tasks.delete_expired_images',
        'schedule': 300.0, 
    },
}