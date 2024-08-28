from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.urls import reverse 
from .models import *
from .forms import *
from HOME_AREA.models import *
from urllib.parse import urlencode
from django.core.cache import cache
from datetime import timedelta
from HOME_AREA.tasks import send_email
# Create your views here.
from ELEARN_BACKEND.CUSTOME_DECORATOR import user_type_required
def update_status(request):
    if request.method == 'POST':
        status = request.POST.get('status')
        cache_key = f'user_status_{request.user.id}'
        cache.set(cache_key, status, timeout=timedelta(days=30).total_seconds())
        return redirect('STUDENTS:Dashboard')

@user_type_required('student')
def Enroll(request,courseName):
    try:
        print("get out")
        student = STUDENT.objects.get(USER_NAME = request.user.USER_NAME)
        course = COURSES.objects.get(COURSE_NAME = courseName)
        print("user found but student adding failed")
        COURSE_LIST.objects.create(course =course, student = student)
        print("success")


    except:
        pass
    return redirect ('HOME_AREA:index')

def Dashboard(request, studentName = ''):
    print(request.user)
    # this approach to serve both personal and others dashboards 
  
    student_name = request.user.USER_NAME if len(studentName) <2  else studentName
    Can_EDIT = True if  request.user.USER_NAME == student_name else False
    print(student_name)
    student = STUDENT.objects.get(USER_NAME = student_name) 
    courses = COURSE_LIST.objects.filter(student = student).values_list('course', flat = True)
    Courses = COURSES.objects.filter(id__in = courses )

    cash_key = f"user_status_{request.user.id}"
    status = cache.get(cash_key)

    return render(request, 'Dashboard.html',{'courses':Courses, 
    'CAN_EDIT':Can_EDIT,'student':student, 'status':status})

@user_type_required('student')
def DropCourse(request, courseName):

    student = STUDENT.objects.get(USER_NAME = request.user)
    print(f'student user name is {student.USER_NAME} and request user is {type(request.user.USER_NAME)}')
    # to ensure same origin so no other student can drop a course that belong to other one 
    if request.user.USER_NAME == student.USER_NAME:
        print('matching passed')
        course = COURSES.objects.get(COURSE_NAME = courseName)
        deleted = COURSE_LIST.objects.get(student = student, course = course)
        deleted.delete()

        return redirect('STUDENTS:Dashboard')
    else:
        return HttpResponseForbidden("you are not authorized to do this")

@user_type_required('student')
def EditProfileLink(request):
   
    return render(request,'EditProfileForm.html')

def EditProfile(request):
    if request.method == 'POST':
        form = EditStudentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                student = STUDENT.objects.get(USER_NAME = request.user)
                cd = form.cleaned_data
                for key, value in cd.items() :
                    setattr(student, key, value)
                student.save()
                message = "your information updated correctly"
                base_url = reverse('STUDENTS:Dashboard',args=[])
                query_url ={'message':message}
                url_encoded_query = urlencode(query_url)
                full_url = f'{base_url}?{url_encoded_query}'
                return redirect(full_url)
            except:

                return render(request, 'EditProfileForm.html',{'form':form})
        else :
            return render(request, 'EditProfileForm.html',{'form':form})
    else :
        form = EditStudentForm()
        return render(request,'EditProfileForm.html',{'form':form})

@user_type_required('student')
def AddReview(request, courseName):
    if request.method == 'POST':
        opinion = request.POST.get('rev')
        course = COURSES.objects.get(COURSE_NAME = courseName)
        student = STUDENT.objects.get(USER_NAME = request.user)
        review, created = REVIEWS.objects.update_or_create(USER_NAME=student,
                            reviews=course,
                            defaults={'OPINION':opinion}
                            )
        return redirect(reverse('HOME_AREA:Course_Details', args=[courseName]))

    
def RemoveBlockRequest(request, courseName):
    if request.method == 'POST':
        try:
            instruc = COURSES.objects.get(COURSE_NAME = courseName).instructor
            student = STUDENT.objects.get(USER_NAME = request.user).EMAIL
            appeal = request.POST.get('appeal')
            send_email(instruc.EMAIL, appeal)
            send_email(student, f"your message was sent successfully and here is acopy of it {appeal}")
            return redirect('HOME_AREA:index')
        except:
            main_url = reverse('HOME_AREA:Course_Details',args=[courseName])
            return redirect(main_url)

@user_type_required('student')
def AddRating(request, courseName):
    if request.method == 'POST':
        rating = request.POST.get('rate')
        print(rating)
        rate_create = Rating.objects.update_or_create(
            course =COURSES.objects.get(COURSE_NAME = courseName),
            user = STUDENT.objects.get(USER_NAME = request.user),
            defaults={'RATING':rating}
        )
        return redirect(reverse('HOME_AREA:Course_Details',args=[courseName]))







    
    