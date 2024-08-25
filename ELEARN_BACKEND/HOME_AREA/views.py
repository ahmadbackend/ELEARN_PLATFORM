from django.shortcuts import render, redirect
from .models import *
from .forms import *
from .tasks import send_email ,CleanDatabase
#to save generated code in corresponding database class
from INSTRUCTOR.models import CODE_GENERATOR_INSTR, INSTRUCTOR, BLOCK_LIST
from STUDENT.models import CODE_GENERATOR, STUDENT, COURSE_LIST
from random import randint
# using auth to save log ing sessions 
from django.contrib.auth.models import User
from django.contrib.auth import login, logout , authenticate
from .AuthCust import *
from django.urls import reverse 
from django.db.models import Avg

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
def Course_Details(request,courseName):
    if request.user.user_cat == 'instructor':
        # constructing the path using reverse dynamically
        return redirect(reverse('instructor:CourseDetails',args=[courseName]))
    studentName = request.user if request.user  else ""
    
    course = COURSES.objects.get(COURSE_NAME = courseName)
    reviews = REVIEWS.objects.filter(reviews = course)
   
    lectures = course.lectures.all()
    IsEnrolled = False
    Blocked = False
    #if student is blocked cannot access the courses belong to that instructor and need to contact him
    if studentName :
        student = STUDENT.objects.get(USER_NAME = studentName)
        Blocked = BLOCK_LIST.objects.filter(students = student, instructors=course.instructor).exists()
        
        IsEnrolled =  COURSE_LIST.objects.filter(course = course, student = student).exists()
    return render(request,"CourseDetails.html",{'course':course,
                'lectures':lectures, 'reviews':reviews, 
                'enrolled':IsEnrolled, 'blocked':Blocked})

def AccessChatRoom(request, courseName):
    user_name = request.user.USER_NAME
    cour = courseName.split(" ")
    cc=""
    for co in cour:
        cd = co.strip()
        cc+=cd
    print(cc)

    return render(request, 'CourseChatRoom.html',{'course':cc,'user':user_name})