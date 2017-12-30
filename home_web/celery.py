import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'home_web.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Dev')

import configurations  # noqa
configurations.setup()

app = Celery('home_web')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):  # pragma: no cover
    print("Request: {0!r}".format(self.request))
