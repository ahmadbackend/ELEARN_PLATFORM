from rest_framework import serializers
from .models import *

from HOME_AREA.serializers import Courses_Serializer
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = STUDENT
        exclude = ["is_active"]
        depth = 1

class CourseStudentSerializer(serializers.ModelSerializer):
    course = Courses_Serializer()
    student = StudentSerializer()
    class Meta:
        model = COURSE_LIST
        fields = "__all__"
        depth = 1

     
class LogInSerializer(serializers.Serializer):
    USER_NAME = serializers.CharField(required=True)
    EMAIL =serializers.EmailField(required=True)
    PASSWORD = serializers.CharField(required=True)
   
    def validate(self, data):
        user_name = data.get('USER_NAME')

        email = data.get('EMAIL')
        password = data.get('PASSWORD')
        try:
            student = get_object_or_404(STUDENT, USER_NAME = user_name,
            PASSWORD = password, EMAIL = email)
            if student.ISactive:
                return data
            else:
                raise ValidationError({"message": "User is valid but not active", "Isactive": False}) 
        except:
            raise ValidationError("Invalid credentials")

class VrifySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CODE_GENERATOR
        fields = ["ACTIVATION_CODE","EMAIL"]
class ForgetPassSerializer(serializers.Serializer):
    EMAIL = serializers.EmailField(required=True)