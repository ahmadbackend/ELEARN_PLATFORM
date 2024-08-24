from django.urls import path
from . import views
# declaring namespace so i can use these views from anywhere 
app_name = 'STUDENTS'
urlpatterns = [
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

]