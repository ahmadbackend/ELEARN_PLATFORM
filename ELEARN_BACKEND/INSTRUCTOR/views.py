from django.shortcuts import render, redirect
from django.views.generic import DetailView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.urls import reverse
from HOME_AREA.models import COURSES, LECTURES
from STUDENT.models import COURSE_LIST, STUDENT
from .models import *
from .forms import *
from ELEARN_BACKEND.CUSTOME_DECORATOR import *
from django.core.cache import cache
from datetime import timedelta
# Create your views here.
def index(request):
    user = request.user if str(request.user) != "AnonymousUser" else False
    print(f'user is {request.user.user_cat}')

    courses = COURSES.objects.all()
    return render (request , 'index.html',{'courses':courses, "user":user})

def CourseDetails(request, courseName):

    course = COURSES.objects.get(COURSE_NAME = courseName)
    lectures = course.lectures.all()
    return render(request, 'course-details.html',{'course':course,'lectures':lectures})

def update_status(request):
    if request.method == 'POST':
        status = request.POST.get('status')
        cache_key = f'user_status_{request.user.id}'
        cache.set(cache_key, status, timeout=timedelta(days=30).total_seconds())
        return redirect('instructor:Dashboard')


#show his courses to edit any as links
# number of enrolled students per course
#ability to send email to course enrolled -> another function =link inside dashboard
#authenticate the user as instructor
class InstructorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return  self.request.user.user_cat == 'instructor'

    def handle_no_permission(self):
        raise Http404  
#view students
class LearnersList(InstructorRequiredMixin, ListView): 
    model = STUDENT
    template_name = 'LearnersList.html'
    context_object_name = 'learners'

    def get_queryset(self):
        learners = {}
        instru = INSTRUCTOR.objects.get(USER_NAME=self.request.user)  # Use self.request.user
        courses = COURSES.objects.filter(instructor=instru)
        
        for course in courses:
            course_students = COURSE_LIST.objects.filter(course=course)
            student_list = [cs.student for cs in course_students] 
            learners[course] = student_list
        
        return learners

# View a Course
class CourseDetailView(InstructorRequiredMixin, DetailView):
    model = COURSES
    template_name = 'course_detail.html'
    context_object_name = 'course'

    def get_object(self, queryset=None):
        return COURSES.objects.get(COURSE_NAME=self.kwargs['courseName'])

class CourseDeleteView(InstructorRequiredMixin, DeleteView):
    model = COURSES
    template_name = 'course_confirm_delete.html'
    context_object_name = 'course'

    def get_object(self, queryset=None):
        return COURSES.objects.get(COURSE_NAME=self.kwargs['courseName'])

    def get_success_url(self):
        return redirect('instructor:index') 

@user_type_required('instructor')
def Dashboard(request):
    instruct = INSTRUCTOR.objects.get(USER_NAME = request.user)
    print(instruct)
   
    courses = COURSES.objects.filter(instructor = instruct)
    COURSES_STUDENTS= {}
    for coursY in courses:
        students = COURSE_LIST.objects.filter(course=coursY).count()
        COURSES_STUDENTS[coursY]=students
    cash_key = f"user_status_{request.user.id}"
    status = cache.get(cash_key)
   
    return render(request,'DTashboard.html',{'courses':COURSES_STUDENTS,'status':status}) 

@user_type_required('instructor')
def CreateCourse(request):
    if request.method == 'POST':
        form = CreateForm(request.POST, request.FILES)
        print(request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            instruc = INSTRUCTOR.objects.get(USER_NAME = request.user)
            try:
                cour = COURSES.objects.create(COURSE_NAME=cd["COURSE_NAME"], COVER_PHOTO = cd["COVER_PHOTO"], IsDraft=cd["IsDraft"], instructor=instruc)
                return redirect ('instructor:Dashboard')
            except:
                print("why we here")
                return render (request , "CreateCourse.html", {'form':form})
        else:
            print(form.errors)
            return render (request , "CreateCourse.html", {'form':form})
    else:
        form = CreateForm()
        return render (request , "CreateCourse.html", {'form':form})


def AddLecture(request, courseName):
    if request.method == 'POST':
        form = AddLectureForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            Course = COURSES.objects.get(COURSE_NAME=courseName)
            instru = INSTRUCTOR.objects.get(USER_NAME = request.user)
            lecture = LECTURES.objects.create(**cd, course=Course)
            message ="lecture added successfully"
            return redirect('instructor:Dashboard')
        else:
            return render(request, 'instructor:AddLecture.html', {'form':form, 'course':courseName})

    else:
        form = AddLectureForm()
        return render(request, 'instructor:AddLecture.html', {'form':form, 'course':courseName})

def HandlLectures(request,courseName):
    Course = COURSES.objects.get(COURSE_NAME = courseName)
    lectures = LECTURES.objects.filter(course = Course)
    print(lectures.count())
    return render(request, 'HandlLectures.html',{'lectures':lectures})
    
def Publish(request, courseName):
    instr = INSTRUCTOR.objects.get(USER_NAME = request.user)
    course = COURSES.objects.get(COURSE_NAME=courseName, instructor= instr)
    course.IsDraft = False
    course.save()
    message= "your course published successfully"
    return redirect('instructor:Dashboard')
def Block(request):
    if request.method == 'POST':
        cd = request.POST
        try:
            BAD_STUDENT = STUDENT.objects.get(USER_NAME = cd["blocked"])
            instruc = INSTRUCTOR.objects.get(USER_NAME = request.user)
            blocked = BLOCK_LIST.objects.add(students = BAD_STUDENT , instructors = instruc )
            blocked.save()
        except:
            message = "no user matched your input "
           
        return redirect('instructor:Dashboard')

       
def UnBlock(request):
    if request.method == 'POST':
        cd = request.POST
        try:
            BAD_STUDENT = STUDENT.objects.get(USER_NAME = cd["unblocked"])
            instruc = INSTRUCTOR.objects.get(USER_NAME = request.user)
            unblocked = BLOCK_LIST.objects.delete(students = BAD_STUDENT , instructors = instruc )
            unblocked.save()
            message = "learner unblocked successfully"
        except:
            message = "no user matched your input"
           
        return redirect('instructor:Dashboard')    
"""
@user_type_required(user='instructor')
def DeleteCourse(request, courseName):
    pass

@user_type_required(user='instructor')
def EditCourse(request, courseName):
    pass

@user_type_required(user='instructor')
def ViewCourse(request, courseName):
    pass
"""