from django.urls import path 
from . import views, forms, REGLOG
app_name ='HOME_AREA'
urlpatterns = [
   #registeration, log in functionalities
    path('INSTRUCTOR_REG',REGLOG.instructor_reg_form, name="instructor_reg_form"),
    path('INSTRUCTOR_LOG',REGLOG.instructor_login , name ="instructor_login"),
    path('STUDENT_REG', REGLOG.student_reg_form, name="student_reg_form"),
    path('STUDENT_LOG',REGLOG.student_login, name ="student_login"),
    path("VERIFICATION/<str:user_type>",REGLOG.Verify , name="Verify" ),
    path("forget/<str:user_type>",REGLOG.Forget , name="Forget" ),
    path("logout",REGLOG.Logout, name='Logout'),
    path("editpass/<str:user_type>",REGLOG.EditPass, name='EditPass'),

    #courses functionalities
    path("Course_Details/<str:courseName>",views.Course_Details, name= 'Course_Details'),
    path('',views.index , name ="index"),
]
