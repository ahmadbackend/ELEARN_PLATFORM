"""
/api/v1/ - the whole REST surface in one place so a frontend developer can read it top to bottom.

auth/        register, login (returns a Bearer token), activation and password reset
me/          the logged in user: profile, dashboard status, own courses
courses/     public catalogue, per-course lectures / reviews / ratings / chat room
students/    public learner pages          instructors/   public tutor pages
student/     learner actions on a course   instructor/    tutor management
peer-chats/  learner <-> tutor private conversations
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from HOME_AREA import APIs as home
from INSTRUCTOR import APIs as instructor
from STUDENT import APIs as student

app_name = 'api'

router = DefaultRouter()
router.register('courses', home.CourseViewSet, basename='course')
router.register('instructor/courses', instructor.InstructorCourseViewSet, basename='instructor-course')

lecture_list = instructor.InstructorLectureViewSet.as_view({'get': 'list', 'post': 'create'})
lecture_detail = instructor.InstructorLectureViewSet.as_view(
    {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})

urlpatterns = [
    # ---- auth
    path('auth/register/student/', home.RegisterStudentAPI.as_view(), name='register-student'),
    path('auth/register/instructor/', home.RegisterInstructorAPI.as_view(), name='register-instructor'),
    path('auth/login/', home.LoginAPI.as_view(), name='login'),
    path('auth/logout/', home.LogoutAPI.as_view(), name='logout'),
    path('auth/activate/', home.ActivateAPI.as_view(), name='activate'),
    path('auth/password/forgot/', home.ForgotPasswordAPI.as_view(), name='password-forgot'),
    path('auth/password/reset/', home.ResetPasswordAPI.as_view(), name='password-reset'),

    # ---- current user
    path('me/', home.MeAPI.as_view(), name='me'),
    path('me/status/', home.MeStatusAPI.as_view(), name='me-status'),
    path('me/courses/', home.MeCoursesAPI.as_view(), name='me-courses'),

    # ---- public profiles
    path('students/<str:username>/', student.StudentProfileAPI.as_view(), name='student-profile'),
    path('instructors/<str:username>/', instructor.InstructorProfileAPI.as_view(), name='instructor-profile'),

    # ---- learner actions on a course
    path('student/courses/<int:pk>/enroll/', student.EnrollmentAPI.as_view(), name='student-enroll'),
    path('student/courses/<int:pk>/review/', student.MyReviewAPI.as_view(), name='student-review'),
    path('student/courses/<int:pk>/rating/', student.MyRatingAPI.as_view(), name='student-rating'),
    path('student/courses/<int:pk>/appeal/', student.AppealAPI.as_view(), name='student-appeal'),

    # ---- tutor management (courses themselves come from the router below)
    path('instructor/courses/<int:course_pk>/lectures/', lecture_list, name='instructor-lecture-list'),
    path('instructor/courses/<int:course_pk>/lectures/<int:pk>/', lecture_detail, name='instructor-lecture-detail'),
    path('instructor/learners/', instructor.LearnersAPI.as_view(), name='instructor-learners'),
    path('instructor/blocks/', instructor.BlockListAPI.as_view(), name='instructor-blocks'),
    path('instructor/blocks/<str:username>/', instructor.BlockDetailAPI.as_view(), name='instructor-block-detail'),

    # ---- peer chat
    path('peer-chats/', home.PeerChatListAPI.as_view(), name='peer-chat-list'),
    path('peer-chats/<str:instructorName>/<str:studentName>/', home.PeerChatRoomAPI.as_view(), name='peer-chat-room'),
]

urlpatterns += router.urls
