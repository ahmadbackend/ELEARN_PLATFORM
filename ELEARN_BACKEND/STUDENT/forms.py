from django.forms import ModelForm
from .models import STUDENT
from django import forms

class EditStudentForm(ModelForm):
    class Meta:
        model = STUDENT
        fields = ['PASSWORD','FIRST_NAME','LAST_NAME','PICTURE']