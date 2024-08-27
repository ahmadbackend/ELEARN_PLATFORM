from django.urls import path
from . import views, APIs

app_name ='instructor'
urlpatterns = [
    path('CourseDetails/<str:courseName>',views.CourseDetails, name='CourseDetails'),
    path('Dashboard/',views.Dashboard, name='Dashboard'),
    path('CreateCourse',views.CreateCourse, name='CreateCourse'),
    path('course/<str:courseName>/',views.CourseDetailView.as_view(), name='course_detail'),
    path('course/<str:courseName>/delete/',views.CourseDeleteView.as_view(), name='course_delete'),
    path('Block', views.Block, name = 'Block'),
    path('UnBlock', views.UnBlock, name = 'UnBlock'),
    path('AddLecture/<str:courseName>', views.AddLecture, name = 'AddLecture'),
    path('HandlLectures/<str:courseName>', views.HandlLectures, name = 'HandlLectures'),
    path('Publish/<str:courseName>/', views.Publish, name = 'Publish'),
    path('Learners', views.LearnersList.as_view(), name = 'Learners'),
    path('update_status',views.update_status, name = 'update_status'),

    #APIS
    path('APIs/InstructorAPI/<str:USER_NAME>', APIs.InstructorAPI.as_view(), name = 'InstructorAPI'),
    path('',views.index, name='index')
]

"""
    path('EditCourse/<str:courseName', views.EditCourse, name ='EditCourse'),
    path('DeleteCourse/<str:courseName', views.DeleteCourse, name = 'DeleteCourse'),
    path('ViewCourse/<str:courseName>', views.ViewCourse, name = 'ViewCourse'),
"""