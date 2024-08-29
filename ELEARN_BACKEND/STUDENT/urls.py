from django.urls import path
from . import views , APIs
# declaring namespace so i can use these views from anywhere 
app_name = 'STUDENTS'
urlpatterns = [
    #dashboard area
    path('Dashboard/<str:studentName>', views.Dashboard, name = 'DashboardWithUserName'),
    path('Dashboard', views.Dashboard, name = 'Dashboard'),

    path('DropCourse/<str:courseName>', views.DropCourse, name = 'DropCourse'),
    path('EditProfileLink',views.EditProfileLink , name = 'EditProfileLink'),
    path('EditProfile',views.EditProfile, name = 'EditProfile'),
    path('update-status/', views.update_status, name='update_status'),
    path('AddReview/<str:courseName>', views.AddReview, name = 'AddReview'),
    path('RemoveBlockRequest/<str:courseName>',views.RemoveBlockRequest, name = 'RemoveBlockRequest'),
    path('AddRating/<str:courseName>', views.AddRating, name = 'AddRating'),

    path('enrol/<str:courseName>/', views.Enroll, name='Enroll'),  # Make sure there is a trailing slash

    #student APIs area################
    path('APIs/Forms/ForgetPassStudentAPI',APIs.ForgetPassStudentAPI.as_view(), name = 'ForgetPassStudentAPI'),
    path('APIs/Forms/VerifyStudentAPI',APIs.VerifyStudentAPI.as_view(), name = 'VerifyStudentAPI'),
    path('APIs/Forms/StudentLogAPI',APIs.StudentLogAPI.as_view(), name = 'StudentLogAPI'),
    path('APIs/Forms/StudentReg',APIs.StudentReg.as_view()),
    path('APIs/<str:course__COURSE_NAME>',APIs.COURSE_student_APIs.as_view()),
    # to avoid collision with the above url
    path('API/<str:USER_NAME>', APIs.StudentApi.as_view()),
   


]