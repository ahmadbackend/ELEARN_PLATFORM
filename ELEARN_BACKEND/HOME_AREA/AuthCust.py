from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from STUDENT.models import STUDENT  
from INSTRUCTOR.models import INSTRUCTOR
from django.contrib.auth.hashers import check_password
from django.utils import timezone

class StudentBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            student = STUDENT.objects.get(EMAIL=username,PASSWORD=password)
            #if check_password(password, student.PASSWORD):  # Assuming you're using hashed passwords
            student.last_login = timezone.now()  # Update last_login
            student.save(update_fields=['last_login'])  # Save the change
            return student
        except STUDENT.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return STUDENT.objects.get(pk=user_id)
        except STUDENT.DoesNotExist:
            return None

class InstructorBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            instructor = INSTRUCTOR.objects.get(EMAIL=username, PASSWORD=password)
            instructor.last_login = timezone.now()  # Update last_login
            instructor.save(update_fields=['last_login'])  # Save the change
            return instructor
        except INSTRUCTOR.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return INSTRUCTOR.objects.get(pk=user_id)
        except INSTRUCTOR.DoesNotExist:
            return None

