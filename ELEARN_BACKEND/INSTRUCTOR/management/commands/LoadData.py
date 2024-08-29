import os 
import django
import sys
import csv

from django.conf import settings
from STUDENT.models import *
from INSTRUCTOR.models import *
from HOME_AREA.models import *
from django.core.management.base import BaseCommand
from django.core.files.images import  ImageFile


#flushing
os.environ.setdefault('DJANGO_SETTING_MODULES','ELEARN_BACKEND.settings')
print("success")
django.setup()
#FIRST_NAME,LAST_NAME,USER_NAME,EMAIL,PHONE,PICTURE,PASSWORD,Isactive

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        print("Command executed successfully.")
        instructors_csv_path =os.path.join(settings.BASE_DIR, 'INSTRUCTOR','CSVs', 'instructor.csv')
        students_csv_path = os.path.join(settings.BASE_DIR, 'INSTRUCTOR','CSVs', 'student.csv')
        pictures_folder = os.path.join(settings.BASE_DIR, 'INSTRUCTOR','ELEARN_PICS')
        # Your data loading logic goes here
        with open(instructors_csv_path, 'r') as instructors_file:
            reader = csv.DictReader(instructors_file)
            for idx, row in enumerate(reader, start=1):
                picture_filename = f"image-{idx}.jpg"  # Match image-1, image-2, etc.
                picture_path = os.path.join(pictures_folder, picture_filename)

                if os.path.exists(picture_path):
                    with open(picture_path, 'rb') as picture_file:
                        django_image_file = ImageFile(picture_file, name=picture_filename)  # Wrap the image file in an ImageFile object

                        instr, created = INSTRUCTOR.objects.get_or_create(
                            FIRST_NAME=row['FIRST_NAME'],
                            LAST_NAME=row['LAST_NAME'],
                            USER_NAME=row['USER_NAME'],
                            EMAIL=row['EMAIL'],
                            PHONE=row['PHONE'],
                            PASSWORD=row['PASSWORD'],
                            Isactive=True,
                        )
                        instr.PICTURE.save(row['USER_NAME'], django_image_file)  # Save the image file to the PICTURE field
                