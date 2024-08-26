from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
# instead of importing i used lazy loading by using appname.model string
# Create your models here.
class STUDENT(models.Model):
    FIRST_NAME = models.CharField(max_length=50 , null=False , blank=False)
    LAST_NAME = models.CharField(max_length=50 , null=False , blank=False)
    USER_NAME = models.CharField(max_length=50 , null=False , blank=False, unique=True)
    EMAIL = models.EmailField(null=False , blank=False, unique=True)
    PHONE = models.CharField(max_length=15 , null=False, blank=False, unique=True)
    last_login = models.DateTimeField(null=True, blank=True)  # Add last_login field

    PICTURE = models.ImageField(upload_to='images/', blank=True, null= True)
    PASSWORD = models.CharField(null=False, blank=False, max_length=12,
     validators=[
            MinLengthValidator(8),  # Minimum length of 8 characters
            RegexValidator(
                regex=r'^(?=.*[a-z])(?=.*\d)[a-zA-Z\d]{8,}$',
                message="Password must contain at least one lowercase letter and one digit.",
            ),
        ]
    )
    Isactive = models.BooleanField(default = False)
    #useless just to overcome basebackend class and apis requirements
    is_active = models.BooleanField(default = True)

    #all courses that student registered for 
    courseList = models.ManyToManyField('HOME_AREA.COURSES', through='COURSE_LIST')

    def __str__(self) :
        return self.USER_NAME
    
    @property
    def user_cat(self):
        return "student"


    class Meta:
         verbose_name_plural = "Students"
         permissions=[
            ("ENROLL","LEAVE_REVIEW")
         ]

class COURSE_LIST(models.Model):
    student = models.ForeignKey('STUDENT', on_delete=models.DO_NOTHING)
    course = models.ForeignKey('HOME_AREA.COURSES',  on_delete=models.DO_NOTHING)
# verifier user (register, edit password, delete account, ..etc)
class CODE_GENERATOR(models.Model):
    USER_VERIFIER = models.ForeignKey('STUDENT', on_delete=models.CASCADE)
    ACTIVATION_CODE = models.CharField(max_length=6)
    EMAIL = models.EmailField(null=True,blank=True)

