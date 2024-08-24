from __future__ import absolute_import, unicode_literals # must be first line 
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE","ELEARN_BACKEND.settings")

app = Celery("ELEARN_BACKEND")
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
#test that it works 
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')