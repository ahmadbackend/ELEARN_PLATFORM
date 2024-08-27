from rest_framework import serializers
from .models import *
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

class InstructorSerializer(serializers.ModelSerializer):

    class Meta:
        model = INSTRUCTOR
        exclude=["is_active"]
        depth = 1