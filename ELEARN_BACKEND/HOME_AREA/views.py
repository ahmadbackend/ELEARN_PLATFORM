from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.http import JsonResponse
from .tasks import send_email ,CleanDatabase
from django.views.decorators.csrf import csrf_exempt
import json
#to save generated code in corresponding database class
from INSTRUCTOR.models import CODE_GENERATOR_INSTR, INSTRUCTOR, BLOCK_LIST
from STUDENT.models import CODE_GENERATOR, STUDENT, COURSE_LIST
from random import randint
from django.contrib.auth.models import AnonymousUser
# using auth to save log ing sessions 
from django.contrib.auth.models import User
from django.contrib.auth import login, logout , authenticate
from .AuthCust import *
from django.urls import reverse 
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType

# Create your views here.
#home page will produce all courses and wil have pagination and other things (landing page)
def index(request):
    user = request.user if str(request.user) != "AnonymousUser" else False
   

    courses = COURSES.objects.all()
    #create average rating 
    courseDict={}
    for course in courses:
        avg_rate = course.rating_set.aggregate(Avg('RATING')).get('RATING__avg')
        print(f'avg_rate {avg_rate}')
        total_raters = course.rating_set.all().count()
        print(total_raters)
        courseDict[course] = [avg_rate if avg_rate != None else 0,total_raters]
        print(courseDict[course])
    return render (request , 'index.html',{'courses':courseDict, "user":user})
# in this method we display the course details and if user is enrolled or not 
def Course_Details(request, courseName):
    course = COURSES.objects.get(COURSE_NAME = courseName)
    reviews = REVIEWS.objects.filter(reviews = course)
    lectures = course.lectures.all()

    print(f'request.user is {request.user}')
    if isinstance(request.user, AnonymousUser):
        print("we are anonymous")
        return render(request, "CourseDetails.html", {
            'course': course,
            'lectures': lectures,
            'reviews': reviews,
            'enrolled': False,
            'blocked': False,
            'user_cat': False
        })
    
    elif request.user.user_cat == 'instructor' and course.instructor.USER_NAME != request.user.USER_NAME:
            # constructing the path using reverse dynamically
        return redirect(reverse('instructor:CourseDetails',args=[courseName]))
    WatcherName = request.user.USER_NAME
    user_cat = request.user.user_cat

    #if student is blocked cannot access the courses belong to that instructor and need to contact him
    if WatcherName and user_cat == 'student' :
        student = STUDENT.objects.get(USER_NAME = WatcherName)
        Blocked = BLOCK_LIST.objects.filter(students = student, instructors=course.instructor).exists()
        
        IsEnrolled =  COURSE_LIST.objects.filter(course = course, student = student).exists()
    elif WatcherName and user_cat == 'instructor':
        IsEnrolled = True
        Blocked = False
    return render(request, "CourseDetails.html", {'course':course,
                'lectures':lectures, 'reviews':reviews, 
                'enrolled':IsEnrolled, 'blocked':Blocked , 'user_cat':user_cat})

def AccessChatRoom(request, courseName, userCat):
    user_name = request.user.USER_NAME
    course = COURSES.objects.get(COURSE_NAME = courseName)

    #getting all chat related to that course 
    two_weeks_ago = timezone.now() - timedelta(days=14)
    # to fixchannel group name that refuse to contain spaces 
    cour = courseName.split(' ')
    cc= ""
    for co in cour:
        cd = co.strip()
        cc+=cd

    chats = ChatRoom.objects.filter(courseRoom = course, TimeStamp__gte = two_weeks_ago)
        
    return render(request, 'CourseChatRoom.html',
                            {'course':cc,
                            'user':request.user, 
                            'userName':user_name, 
                            'chats':chats,
                            'userCat':userCat,
                            'coursy':courseName})
@csrf_exempt
def SaveTOchat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        message = data["message"]
        # here creating a way so we can add student or instructor to the chat database under same field sender
        userName = STUDENT.objects.get(USER_NAME = data["userName"]) if data['userCat'] =='student' else INSTRUCTOR.objects.get(USER_NAME = data["userName"])
        content = ContentType.objects.get_for_model(STUDENT) if  data['userCat'] =='student' else ContentType.objects.get_for_model(INSTRUCTOR)
        course = COURSES.objects.get(COURSE_NAME = data["course"])
        #kicking the bad user out of the chat immediately
        if BLOCK_LIST.objects.filter(students = userName, instructors = course.instructor).exists():
            return redirect('HOME_AREA:index')
        ChatRoom.objects.create(message = message, courseRoom = course, 
                                object_id = userName.id,
                                content_type = content)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed', 'error': 'Invalid request method'})
