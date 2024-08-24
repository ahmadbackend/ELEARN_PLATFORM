from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
#Create your models here.
class INSTRUCTOR(models.Model):
    FIRST_NAME = models.CharField(max_length=50 , null=False , blank=False)
    LAST_NAME = models.CharField(max_length=50 , null=False , blank=False)
    USER_NAME = models.CharField(max_length=50 , null=False , blank=False, unique=True)
    EMAIL = models.EmailField(null=False , blank=False, unique=True)
    last_login = models.DateTimeField(null=True, blank=True)  # Add last_login field

    PHONE = models.CharField(max_length=15 , null=False, blank=False, unique=True)
    PASSWORD = models.CharField(null=False, blank=False, max_length=12,
     validators=[
            MinLengthValidator(8),  # Minimum length of 8 characters
            RegexValidator(
                regex=r'^(?=.*[a-z])(?=.*\d)[a-zA-Z\d]{8,}$',
                message="Password must contain at least one lowercase letter and one digit.",
            ),
        ]
    )
    PICTURE = models.ImageField(upload_to="images/", null=False, blank=False) #optioanl pic
    block_list = models.ManyToManyField('STUDENT.STUDENT', through='BLOCK_LIST')
    Isactive = models.BooleanField(default = False)
    def __str__(self):
        return self.USER_NAME
    
    @property
    def user_cat(self):
        return "instructor"

    class META:
        verbose_name_plural = "Instructors"
        permissions = [
            ("BLOCK_STUDENT","ADD_LECTURES","VIEW_STUDENTS","DELETE_COURSE","SEND_MAIL")
        ]
class BLOCK_LIST(models.Model):
    students = models.ForeignKey('STUDENT.STUDENT',  on_delete=models.DO_NOTHING , related_name="students")
    instructors = models.ForeignKey(INSTRUCTOR,  on_delete=models.DO_NOTHING, related_name="instructors")
#table to generate code and email to verify user to complete (registeration, update password, delete account)(prevent bots)
class CODE_GENERATOR_INSTR(models.Model):
    USER_VERIFIER = models.ForeignKey('INSTRUCTOR', on_delete=models.CASCADE)
    ACTIVATION_CODE = models.CharField(max_length=6)
    EMAIL = models.EmailField(null=True,blank=True)

