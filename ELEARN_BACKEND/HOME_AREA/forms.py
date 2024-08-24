from django.forms import ModelForm
from STUDENT.models import STUDENT ,CODE_GENERATOR
from INSTRUCTOR.models import INSTRUCTOR ,CODE_GENERATOR_INSTR
from django import forms
from .models import COURSES
from django.core.exceptions import ValidationError

class Course_Details(ModelForm):
    class Meta:
        model = COURSES
        fields="__all__"
class student(ModelForm):
    PASSWORD = forms.CharField(widget=forms.PasswordInput)


    class Meta:
        model = STUDENT
        fields =["FIRST_NAME","LAST_NAME","USER_NAME","EMAIL","PHONE","PASSWORD","PICTURE"]


class instructor(ModelForm):
    PASSWORD = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = INSTRUCTOR
        fields =["FIRST_NAME","LAST_NAME","USER_NAME","EMAIL","PHONE","PASSWORD","PICTURE"]

class LogForm(forms.Form):
    USER_NAME = forms.CharField(required=True)
    EMAIL =forms.EmailField(required=True)
    PASSWORD = forms.CharField(widget=forms.PasswordInput(), required=True)


class VerifyFormStudent(ModelForm):
    ACTIVATION_CODE = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = CODE_GENERATOR
        fields = ["ACTIVATION_CODE","EMAIL"]

class VerifyFormInstructor(ModelForm):
    ACTIVATION_CODE = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = CODE_GENERATOR_INSTR
        fields = ["ACTIVATION_CODE","EMAIL"]


class ForgetForm(forms.Form):
    EMAIL = forms.EmailField()

class EditPasswordForm(forms.Form):
    ACTIVATION_CODE = forms.CharField()
    EMAIL =forms.EmailField()
    PASSWORD = forms.CharField(widget=forms.PasswordInput())
    CONFIRM_PASSWORD = forms.CharField(widget=forms.PasswordInput())
    #validated that password and confirmed password are the same 
    def clean(self):
        cleaned_data =super().clean()
        password= cleaned_data.get('PASSWORD')
        confrimPass= cleaned_data.get("CONFIRM_PASSWORD")
        if password != confrimPass:
            print(f"password is {password} and conf password is {confrimPass}")
            raise ValidationError("password and confirmed password do not match please recheck")
        else :
            return cleaned_data
        
