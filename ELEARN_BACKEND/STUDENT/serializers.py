from rest_framework import serializers
from .models import *

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = STUDENT
        fields = "__all__"
        depth = 1