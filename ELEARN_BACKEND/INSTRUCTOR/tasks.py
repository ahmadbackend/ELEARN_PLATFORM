from celery import shared_task
from .models import INSTRUCTOR
@shared_task
def DailyClean():
    suspectedBots = INSTRUCTOR.objects.filter(Isactive = False)
    suspectedBots.delete()