from django.forms import ModelForm
from HOME_AREA.models import COURSES, LECTURES
from django import forms
class CreateForm(ModelForm):

    class Meta:
        model = COURSES
        exclude= ["instructor","RATING"]
class AddLectureForm(ModelForm):

    class Meta:
        model = LECTURES
        exclude = ['course']

class BlockForm(forms.Form):
    BLOCKED_USER = forms.CharField(max_length=50)