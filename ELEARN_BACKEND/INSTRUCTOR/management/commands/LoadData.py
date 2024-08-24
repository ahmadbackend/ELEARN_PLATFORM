import os 
import django
import sys
import csv
from django.conf import settings
from STUDENT.models import *
from INSTRUCTOR.models import *
from django.core.management.base import BaseCommand

os.environ.setdefault('DJANGO_SETTING_MODULES','ELEARN_BACKEND.settings')
print("success")
django.setup()

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        print("Command executed successfully.")
        comments = os.path.join(settings.BASE_DIR,'ELEARN_BACKEND','CSVs','instructor.csv')
        with open(comments,'r') as comment:
            reader = csv.DictReader(comment)
            for row in reader:
                print(row)

        # Your data loading logic goes here
        pass