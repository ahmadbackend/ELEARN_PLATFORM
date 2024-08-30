from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# each course will have many reviews 
class REVIEWS(models.Model):
    USER_NAME =  models.ForeignKey( 'STUDENT.STUDENT', on_delete=models.CASCADE) 
    OPINION =  models.CharField(max_length=5000 , null=True , blank=True)
    reviews = models.ForeignKey('COURSES', on_delete=models.CASCADE , blank=True, null=True) 
    WRITING_DATE = models.DateTimeField(auto_created=True, auto_now_add=True, null = True)

    class Meta:
        ordering = ['-WRITING_DATE']


# each lecture will have a discussion area  beside the chat room  or alternative if failed to create chat room
class COMMENTS(models.Model):
    USER_NAME =  models.ForeignKey( 'STUDENT.STUDENT', on_delete=models.CASCADE)
    COMMENT =  models.CharField(max_length=5000 , null=True , blank=True)
    discussion = models.ForeignKey('LECTURES', on_delete=models.CASCADE, blank=True, null=True)
    WRITING_DATE = models.DateTimeField(auto_created=True, auto_now_add=True, null = True)

    class META:
        verbose_name_plural = "Comments"
        ordering = ['WRITING_DATE']
        

class LECTURES(models.Model):
    NAME = models.CharField(max_length=500 , null=False , blank=False)
    VIDEO = models.FileField( upload_to="videos/" , validators=[FileExtensionValidator(["mkv","mp3","mp4"])],blank=True) #mandatory 
    ADDITIONAL_FILES = models.FileField(upload_to="files/", null=True, blank=True , validators=[FileExtensionValidator(["zip","rar"])]) #optional
    course = models.ForeignKey('COURSES', on_delete=models.CASCADE, related_name='lectures')


    def __str__(self):
        return self.NAME

    class META:
        verbose_name_plural = "Lectures"
    
class COURSES(models.Model):

    COURSE_NAME = models.CharField(max_length=500 , null=False , blank=False , unique=True)
    COVER_PHOTO = models.ImageField(blank=False, null=False,upload_to="images/")
    instructor = models.ForeignKey('INSTRUCTOR.INSTRUCTOR', on_delete=models.CASCADE, related_name='instruct')
    PUBLICATION_DATE = models.DateTimeField(auto_created = True, auto_now_add = True)
    IsDraft = models.BooleanField(default=False) # to separate the drafts from publishable courses
    

    def __str__(self) :
        return self.COURSE_NAME

    class META:
         verbose_name_plural  = "Courses"

class Rating(models.Model):
    rating_choices = [
        (2, "2"),
        (4, "4"),
        (1, "1"),
        (5, "5"),
        (3, "3")
    ]
    RATING = models.IntegerField(choices=rating_choices, blank=True, null=True)
    user = models.ForeignKey('STUDENT.STUDENT', on_delete=models.CASCADE)
    course = models.ForeignKey('COURSES', on_delete=models.CASCADE)
    #both student and teacher will inherit from it 



class ChatRoom(models.Model):
    message = models.CharField(max_length = 250, blank=True, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    #so both student and instructor can contribute to the chat 
    sender = GenericForeignKey('content_type', 'object_id')
    TimeStamp =models.DateTimeField(auto_now_add=True)
    courseRoom = models.ForeignKey(COURSES, on_delete=models.CASCADE)

    class Meta:
        ordering = ['TimeStamp']



