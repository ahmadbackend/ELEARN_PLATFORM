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

def instructor_reg_form(request):
    

    if request.method == 'POST' :
        form = instructor(request.POST, request.FILES)#files to handle images
        if form.is_valid():
            
            cd =form.cleaned_data 
            #send an email using celery tasks 
            verification_code = randint(100000,999999)
            message =f"congrats for registering with us kindly use your email and the follow code to complete the registeration {verification_code}"
            send_email(cd["EMAIL"],message)
            new_instrcutor = form.save()
            store_verify = CODE_GENERATOR_INSTR.objects.create(USER_VERIFIER=new_instrcutor,ACTIVATION_CODE=verification_code,EMAIL=cd["EMAIL"])
            veriform = VerifyFormInstructor()
            
            print(request.user)
            return  render(request, "verifier.html",{"user_type":"instructor", "form":veriform}) 

        else :
            print("invalid form ")
            return render (request, 'instructorForm.html',{'form':form})

    else:
        form = instructor()
        return render (request, 'instructorForm.html',{'form':form})


""" 
i know that i could use one function to register both student 
and instructor but i expect to add more feature in each 
"""

def student_reg_form(request):
    

    if request.method == 'POST' :
        form = student(request.POST, request.FILES)
        if form.is_valid():
            
            
            cd =form.cleaned_data 
           
            #sending an email with random 6 digit code to verify the user
            verification_code = randint(100000,999999)
            message =f" congrats for registering with us kindly use your email and the follow code to complete the registeration {verification_code}"
            
            send_email(cd["EMAIL"],message)
            new_student = form.save()
            store_verify = CODE_GENERATOR.objects.create(USER_VERIFIER=new_student,ACTIVATION_CODE=verification_code,EMAIL=cd["EMAIL"])
            verForm = VerifyFormStudent()
            
            return  render(request, "verifier.html",{"user_type":"student","form":verForm}) 
        else :
            print("invalid form ")
            return render (request, 'studentForm.html',{'form':form})

    else:
        form = student()
        return render (request, 'studentForm.html',{'form':form})
 
######################log in methods shall be improved to single method  #############

def student_login(request):
    if request.method == 'POST' :
        form = LogForm(request.POST)
        #this approach to escape form validation for password 
        if form.is_valid():
            data = form.cleaned_data
            email = data["EMAIL"]
            password = data["PASSWORD"]
            student = authenticate(request, username = email, password=password,  backend = "AuthCust.StudentBackend")

            if student is not None:
                if student.Isactive:

                    if login(request, student, backend = "HOME_AREA.AuthCust.StudentBackend"):
                        print(f'User after login: {request.user} (authenticated: {request.user.is_authenticated})')
                    
                    
                        return redirect('HOME_AREA:index')
                    else:
                        return render(request, "student_login.html",{'form':form,"alarm":"login failed"})

                else:
                    return render(request, "student_login.html",{'form':form,"alarm":"please activate your account first your activation code can be in inbox or junk mail"})
            
            
            else:
                return render(request,"student_login.html",{"form":form, "message":"WRONG USER NAME OR PASSWORD"})
            
        else:   
            return render(request,"student_login.html",{"form":form, "message":"invalid input"})
           
    else:
       
        form = LogForm()
        return render (request, 'student_login.html',{'form':form})


def instructor_login(request):
    if request.method == 'POST' :
        form = LogForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            passw = data["PASSWORD"]
            email = data["EMAIL"]
            instr =authenticate(request, username = email , password = passw, backend = "HOME_AREA.AuthCust.InstructorBackend")
            if instr is not None:
                if instr.Isactive == True:
                    login(request, instr, backend = "HOME_AREA.AuthCust.InstructorBackend")
                    return redirect('HOME_AREA:index')
                else:
                     return render(request,"instr_login.html",{"form":form, "alarm":"you have not activated your account yet"})
            else:
                return render(request,"instr_login.html",{"form":form, "message":"WRONG USER NAME OR PASSWORD"})
        else:
                return render(request,"instr_login.html",{"form":form, "message":"invalid input"})

    else:
        form = LogForm()
        return render (request, 'instr_login.html',{'form':form})

###########################user verification ###################

def Verify(request, user_type):
    if request.method == "POST":
        if user_type == "student" :
            form =VerifyFormStudent(request.POST)
            if form.is_valid():
                cd= form.cleaned_data
               
                try:
                    student_tess = CODE_GENERATOR.objects.get(EMAIL=cd["EMAIL"], ACTIVATION_CODE=cd["ACTIVATION_CODE"])
                    if STUDENT.objects.filter(EMAIL=student_tess.EMAIL).exists():
                        student_verified = STUDENT.objects.get(EMAIL=student_tess.EMAIL)
                        student_verified.Isactive=True
                        student_verified.save()

                        #cleaning the database of the useless code 
                        CleanDatabase(student_tess.EMAIL,cd["ACTIVATION_CODE"],CODE_GENERATOR)
                        return redirect('student_login')
                    else:
                        print("Email not found in the database.")
                        return render(request,'verifier.html',{'form':form,'message':"invalid activation code or wrong email",'user_type':'student'})
                except:
                    print("invalid input")
                    return render(request,'verifier.html',{'form':form,'message':"invalid activation code",'user_type':'student'})
        elif user_type == "instructor":
            form = VerifyFormInstructor(request.POST)
            if form.is_valid():
                cd= form.cleaned_data
                try:
                    instructor_test = CODE_GENERATOR_INSTR.objects.get(EMAIL=cd["EMAIL"], ACTIVATION_CODE=cd["ACTIVATION_CODE"])
                    instructor_verified = INSTRUCTOR.objects.get(EMAIL=instructor_test.EMAIL)
                    instructor_verified.Isactive=True
                    instructor_verified.save()
                    CleanDatabase(instructor_test.EMAIL,cd["ACTIVATION_CODE"], CODE_GENERATOR_INSTR)
                    return redirect('HOME_AREA:instructor_login')

                except:
                    print(form.errors)
                    return render(request,'verifier.html',{'form':form,'message':"invalid activation code",'user_type':'instructor'})


    else:
        if user_type == "instructor":
            form = VerifyFormInstructor()
            return render(request , "verifier.html", {"form":form,"user_type":"instructor"}) 
        elif user_type == "student":
            form = VerifyFormStudent()
            return render(request , "verifier.html", {"form":form,"user_type":"student"}) 
        

def Forget(request,user_type):
    if request.method == "POST":
        if user_type == "student" :
            form = ForgetForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                student = STUDENT.objects.get(EMAIL=cd["EMAIL"])

                verification_code = randint(100000,999999)
                message =f" this code was sent based on your request to restore the log in credintial ignore if you do not send it  {verification_code}"
                
                send_email(cd["EMAIL"],message)
                store_verify = CODE_GENERATOR.objects.create(USER_VERIFIER=student,ACTIVATION_CODE=verification_code,EMAIL=cd["EMAIL"])
                print(store_verify)
                restform = EditPasswordForm()
                return render (request, 'editpassword.html',{'form':restform ,'user_type':'student'})
        elif user_type == "instructor" :
            form = ForgetForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                instructor = INSTRUCTOR.objects.get(EMAIL=cd["EMAIL"])

                verification_code = randint(100000,999999)
                message =f" this code was sent based on your request to restore the log in credintial ignore if you do not send it  {verification_code}"
                
                send_email(cd["EMAIL"],message)
                
                store_verify = CODE_GENERATOR_INSTR.objects.create(USER_VERIFIER=instructor,ACTIVATION_CODE=verification_code,EMAIL=cd["EMAIL"])
                print(store_verify)
                restform = EditPasswordForm()
                return render (request, 'editpassword.html',{'form':restform ,'user_type':'instructor'})

    else:
        form = ForgetForm()
        return render (request, 'forget.html',{'form':form ,'user_type':user_type})
###############################dit password method#############################3

def EditPass(request, user_type=None):

    if request.method == "POST":
        if user_type == "student":
            form = EditPasswordForm(request.POST)
            print("exit at start of validation")
            if form.is_valid():
                cd = form.cleaned_data
                try:
                    print(cd)
                    student_tess = CODE_GENERATOR.objects.get(EMAIL=cd["EMAIL"], ACTIVATION_CODE=cd["ACTIVATION_CODE"])
                    
                    student = STUDENT.objects.get(EMAIL = student_tess.EMAIL)
                    print("exit due to student")
                    student.PASSWORD = cd["PASSWORD"]
                    #save the changes to database
                    student.save()
                    message = "you have reset your password successfully if it is not you please go to you account "
                    send_email(cd["EMAIL"],message)
                    #cleaning the database of the useless code 
                    CleanDatabase(student_tess.EMAIL,cd["ACTIVATION_CODE"],CODE_GENERATOR)
                    return redirect('student_login')
                except:
                    print(form.errors)
                    return render (request, "editpassword.html",{'form':form,'user_type':user_type,'message':'invalid input'})
            else:
                    return render (request, "editpassword.html",{'form':form,'user_type':user_type})

        elif user_type == "instructor":
            form = EditPasswordForm(request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                try:
                    instructor_test = CODE_GENERATOR_INSTR.objects.get(EMAIL=cd["EMAIL"], ACTIVATION_CODE=cd["ACTIVATION_CODE"])
                    print('am i here')
                    instructor_verified = INSTRUCTOR.objects.get(EMAIL=instructor_test.EMAIL)
                    print("instructor problem")
                    instructor.PASSWORD = cd["PASSWORD"]
                    instructor.save()
                    message = "you have reset your password successfully if it is not you please go to you account to reset immedtiately  "
                    send_email(cd["EMAIL"],message)
                    #cleaning the database of the useless code 
                    CleanDatabase(instructor.EMAIL,cd["ACTIVATION_CODE"],CODE_GENERATOR_INSTR)
                    return redirect('instructor:instructor_login')
                except:
                    return render (request, "editpassword.html",{'form':form,'user_type':user_type,'message':'invalid input'})
            
        else:
            return redirect('index')
    else:
        form = EditPasswordForm()
        return render (request, "editpassword.html",{'form':form,'user_type':user_type})


def Logout(request):
    logout(request) # destroy session data 
    return redirect('HOME_AREA:index')
