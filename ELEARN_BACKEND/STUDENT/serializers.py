from rest_framework import serializers
from .models import *
from HOME_AREA.serializers import Courses_Serializer
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

     
