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
   



        

