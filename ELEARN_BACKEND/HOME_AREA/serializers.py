from rest_framework import serializers, routers
from .models import * 
from INSTRUCTOR.models import INSTRUCTOR

class InstructorSerializer(serializers.ModelSerializer):
    class Meta:
        model = INSTRUCTOR
        fields = ["USER_NAME"]
class Courses(serializers.ModelSerializer):
    instructor = InstructorSerializer()
    class Meta:
        model = COURSES
        fields = "__all__"

class CourseDetailsSerializer(serializers.ModelSerializer):
    instructor = InstructorSerializer()
    class Meta:
        model = COURSES
        fields = "__all__"