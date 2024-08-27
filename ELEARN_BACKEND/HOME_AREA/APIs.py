from rest_framework import routers, mixins, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from ELEARN_BACKEND.CUSTOME_DECORATOR import user_type_required
from rest_framework.response import Response 
from .serializers import *
from .models import *
@api_view(['GET'])
def Course_list(request):
    # no post allowed from here it is only allowed from instructor area
    if request.method == 'GET':
        queryset = COURSES.objects.all()
        Serializer = Courses_Serializer(queryset , many = True)
        return Response(Serializer.data)
# to use with logged in student  
@api_view(['GET'])
#@permission_classes([IsAuthenticated])
@user_type_required('student')
def CourseDetails_fullview(request, courseName):
    #adding this uselss code to comply with Oopen api
    class CourseDetailsView:
        serializer_class = CourseDetailsSerializer
    if request.method == 'GET':
        queryset = COURSES.objects.get(COURSE_NAME = courseName)
        Serializer = CourseDetailsView.serializer_class(queryset)
        return Response(Serializer.data)


# if i need general view for visitor 
@api_view(['GET'])
def CourseDetails_general(request, courseName):
    class CourseDetailsView:
        serializer_class = CourseDetailsSerializer 
    if request.method == 'GET':
        queryset = COURSES.objects.get(COURSE_NAME = courseName)
        SerializedCourse = CourseDetailsView.serializer_class(queryset)
        return Response(SerializedCourse.data)






