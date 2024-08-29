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
    path('SendToFollowers/<str:courseName>', views.SendToFollowers, name = 'SendToFollowers'),
    path('DeleteLecture/<str:courseName>/<str:lectureName>', views.LectureDeleteView.as_view(), name = 'DeleteLecture'),
    #APIS
    path('APIs/InstructorLogAPI', APIs.InstructorLogAPI.as_view(), name = 'InstructorLogAPI'),
    path('APIs/InstrucotReg', APIs.InstrucotReg.as_view(), name = 'InstrucotReg'),
    path('APIs/InstructorAPI/<str:USER_NAME>', APIs.InstructorAPI.as_view(), name = 'InstructorAPI'),
    path('APIs/CourseCRUDAPI/<int:pk>', APIs.CourseCRUDAPI.as_view()),
    path('APIs/LecturesCRUDsAPI/<str:course__COURSE_NAME>', APIs.LecturesCRUDsAPI.as_view()),
    path('APIS/UNBlockHandlerAPI', APIs.UNBlockHandlerAPI, name = 'UNBlockHandlerAPI'),
    path('APIS/BlookHandlerAPI', APIs.BlookHandlerAPI, name = 'BlookHandlerAPI'),
    path('',views.index, name='index')
]

"""
    path('EditCourse/<str:courseName', views.EditCourse, name ='EditCourse'),
    path('DeleteCourse/<str:courseName', views.DeleteCourse, name = 'DeleteCourse'),
    path('ViewCourse/<str:courseName>', views.ViewCourse, name = 'ViewCourse'),
"""