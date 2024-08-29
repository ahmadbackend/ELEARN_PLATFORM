from rest_framework import serializers
from .models import *
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from HOME_AREA.models import COURSES, LECTURES
class InstructorSerializer(serializers.ModelSerializer):

    class Meta:
        model = INSTRUCTOR
        exclude=["is_active"]
        depth = 1

class CoursCRUDAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = COURSES
        exclude=["instructor",'PUBLICATION_DATE']

class LecturesCRUDserializer(serializers.ModelSerializer):
    class Meta:
        model = LECTURES
        fields = "__all__"

class BlockHandlerSerializer(serializers.Serializer):
    USER_NAME = serializers.CharField(required = True)


class LogInSerializer(serializers.Serializer):
    USER_NAME = serializers.CharField(required=True)
    EMAIL =serializers.EmailField(required=True)
    PASSWORD = serializers.CharField(required=True)
   
    def validate(self, data):
        user_name = data.get('USER_NAME')

        email = data.get('EMAIL')
        password = data.get('PASSWORD')
        try:
            instructor = get_object_or_404(INSTRUCTOR, USER_NAME = user_name,
            PASSWORD = password, EMAIL = email)
            if student.ISactive:
                return data
            else:
                raise ValidationError({"message": "User is valid but not active", "Isactive": False}) 
        except:
            raise ValidationError("Invalid credentials")
   



        

