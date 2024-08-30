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
from django.core.files import File


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
        courses_csv_path =os.path.join(settings.BASE_DIR, 'INSTRUCTOR','CSVs', 'courses.csv')

        lectures_csv_path =os.path.join(settings.BASE_DIR, 'INSTRUCTOR','CSVs', 'lectures.csv')
        reviews_csv_path =os.path.join(settings.BASE_DIR, 'INSTRUCTOR','CSVs', 'reviews.csv')


        pictures_folder = os.path.join(settings.BASE_DIR, 'INSTRUCTOR','ELEARN_PICS')

        # loading instructor data in bulk 
        with open(instructors_csv_path, 'r') as instructors_file:
            reader = csv.DictReader(instructors_file)
            for idx, row in enumerate(reader, start=1):
                picture_filename = f"image-{idx}.jpg"  # Match image-1, image-2, etc.
                picture_path = os.path.join(pictures_folder, picture_filename)

                if os.path.exists(picture_path):
                    with open(picture_path, 'rb') as picture_file:
                        # Wrap the image file in an ImageFile object
                        django_image_file = ImageFile(picture_file, name=picture_filename)  

                        instr, created = INSTRUCTOR.objects.get_or_create(
                            FIRST_NAME=row['FIRST_NAME'],
                            LAST_NAME=row['LAST_NAME'],
                            USER_NAME=row['USER_NAME'],
                            EMAIL=row['EMAIL'],
                            PHONE=row['PHONE'],
                            PASSWORD=row['PASSWORD'],
                            Isactive=True,
                        )
                        # Save the image file to the PICTURE field with same instructor name 
                        instr.PICTURE.save(row['USER_NAME'], django_image_file) 

                        #same as above for student 
        with open(students_csv_path, 'r') as students_file:
            reader = csv.DictReader(students_file)
            for idx, row in enumerate(reader, start=1):
                picture_filename = f"image-{idx}.jpg"  # Match image-1, image-2, etc.
                picture_path = os.path.join(pictures_folder, picture_filename)

                if os.path.exists(picture_path):
                    with open(picture_path, 'rb') as picture_file:
                        # Wrap the image file in an ImageFile object
                        django_image_file = ImageFile(picture_file, name=picture_filename)  

                        student, created = STUDENT.objects.get_or_create(
                            FIRST_NAME=row['FIRST_NAME'],
                            LAST_NAME=row['LAST_NAME'],
                            USER_NAME=row['USER_NAME'],
                            EMAIL=row['EMAIL'],
                            PHONE=row['PHONE'],
                            PASSWORD=row['PASSWORD'],
                            Isactive=True,
                        )
                        # Save the image file to the PICTURE field with same instructor name 
                        student.PICTURE.save(row['USER_NAME'], django_image_file)  
        #COURSE_NAME,COVER_PHOTO,instructor,RATING,PUBLICATION_DATE,IsDraft

        with open(courses_csv_path,'r') as courses:
            reader = csv.DictReader(courses)
            for idx, row in enumerate(reader, start = 1):
                img = f'image-{idx}.jpg'
                picPath = os.path.join(pictures_folder, img)
                instr = INSTRUCTOR.objects.get(USER_NAME = row['instructor'])
                if os.path.exists(picPath):
                    with open(picPath, 'rb') as Img:
                        courseImg = ImageFile(Img, name = img)
                        course, created = COURSES.objects.get_or_create(
                            COURSE_NAME = row['COURSE_NAME'],
                            IsDraft= False,
                            instructor= instr,
                        )
                        course.COVER_PHOTO.save(row['COURSE_NAME'], courseImg)

        #LOADING LECTURES TO COURSES 
        #NAME,VIDEO,ADDITIONAL_FILES,course
        video_path = os.path.join(settings.BASE_DIR, 'INSTRUCTOR','ELEARN_VIDEOS_dummy','sample1.mp4')
        with open(lectures_csv_path, 'r') as lectures:
            reader = csv.DictReader(lectures)
            for  row in reader:
                
                
                # Get the course associated with the lecture
                course = COURSES.objects.get(COURSE_NAME=row['course'])
                
                if os.path.exists(video_path):
                    with open(video_path, 'rb') as video_file:
                        lectureVideo = File(video_file, name=f'{row["NAME"]}.mp4')
                        
                        # Create or get the lecture
                        lecture, created = LECTURES.objects.get_or_create(
                            NAME=row['NAME'],
                            course=course,
                            defaults={'ADDITIONAL_FILES': row['ADDITIONAL_FILES']}
                        )
                        
                        # Save the video to the lecture
                        lecture.VIDEO.save(f'{row["NAME"]}.mp4', lectureVideo)
                else:
                    print("im here in wrong area")
        
        #USER_NAME,OPINION,reviews
        with open(reviews_csv_path,'r') as review:
            reader = csv.DictReader(review)
            for  row in reader :
                
                student  = STUDENT.objects.get(USER_NAME = row['USER_NAME'])
                courset = COURSES.objects.get(COURSE_NAME = row['reviews'])
                   
                rev, created = REVIEWS.objects.get_or_create(
                    USER_NAME = student,
                    OPINION= row['OPINION'],
                    reviews=courset,
                    
                )