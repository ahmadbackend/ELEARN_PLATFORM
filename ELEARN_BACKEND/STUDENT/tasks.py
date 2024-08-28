from celery import shared_task
from .models import STUDENT
@shared_task
def DailyClean():
    suspectedBots = STUDENT.objects.filter(Isactive = False)
    suspectedBots.delete()
    
