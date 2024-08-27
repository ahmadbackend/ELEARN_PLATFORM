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
    
    if request.method == 'GET':
        queryset = COURSES.objects.get(COURSE_NAME = courseName)
        Serializer = CourseDetailsSerializer(queryset)
        return Response(Serializer.data)


# if i need general view for visitor 
@api_view(['GET'])
def CourseDetails_general(request, courseName):
    
    if request.method == 'GET':
        queryset = COURSES.objects.get(COURSE_NAME = courseName)
        SerializedCourse = CourseDetailsSerializer(queryset)
        return Response(SerializedCourse.data)






