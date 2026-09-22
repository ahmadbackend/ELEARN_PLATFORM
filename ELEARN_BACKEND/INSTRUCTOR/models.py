from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator

from HOME_AREA.passwords import PASSWORD_HASH_MAX_LENGTH

#Create your models here.
class INSTRUCTOR(models.Model):
    FIRST_NAME = models.CharField(max_length=50 , null=False , blank=False)
    LAST_NAME = models.CharField(max_length=50 , null=False , blank=False)
    USER_NAME = models.CharField(max_length=50 , null=False , blank=False, unique=True)
    EMAIL = models.EmailField(null=False , blank=False, unique=True)
    last_login = models.DateTimeField(null=True, blank=True)  # Add last_login field

    PHONE = models.CharField(max_length=15 , null=False, blank=False, unique=True)
    # stores a Django password hash, never the raw password (HOME_AREA.passwords).
    # the validators describe what the *raw* password must look like: the serializers
    # read them back off this field to check the input before it is hashed.
    PASSWORD = models.CharField(null=False, blank=False, max_length=PASSWORD_HASH_MAX_LENGTH,
     validators=[
            MinLengthValidator(8),  # Minimum length of 8 characters
            RegexValidator(
                regex=r'^(?=.*[a-z])(?=.*\d)[a-zA-Z\d]{8,12}$',
                message="Password must be 8 to 12 letters and digits, "
                        "with at least one lowercase letter and one digit.",
            ),
        ]
    )
    PICTURE = models.ImageField(upload_to="images/", null=False, blank=False) #optioanl pic
    block_list = models.ManyToManyField('STUDENT.STUDENT', through='BLOCK_LIST')
    is_active = models.BooleanField(default = True)
    Isactive = models.BooleanField(default = False)
    def __str__(self):
        return self.USER_NAME
    
    @property
    def user_cat(self):
        return "instructor"

    # DRF's IsAuthenticated and Django's auth helpers expect these on any user object.
    # STUDENT/INSTRUCTOR do not extend AbstractBaseUser so we provide them by hand
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    # Learners and tutors are not back-office users: the admin site belongs to
    # django.contrib.auth accounts (see HOME_AREA/staff.py). Declaring these
    # explicitly keeps the admin login form rejecting them cleanly, instead of
    # blowing up on a missing attribute if an address happens to collide.
    is_staff = False
    is_superuser = False

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

