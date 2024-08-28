from rest_framework import routers, mixins, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from ELEARN_BACKEND.CUSTOME_DECORATOR import user_type_required
from rest_framework.response import Response 
from .serializers import *
from .models import *
class CourseListView(ListAPIView):
    queryset = COURSES.objects.all()
    serializer_class = Courses_Serializer

# to use with logged in student  
class CourseDetailsFullView(RetrieveAPIView):
    queryset = COURSES.objects.all()
    serializer_class = CourseDetailsSerializer
    lookup_field = 'COURSE_NAME'

    @user_type_required('student')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# if i need general view for visitor 
class CourseDetailsGeneralView(RetrieveAPIView):
    queryset = COURSES.objects.all()
    serializer_class = CourseDetailsSerializer
    lookup_field = 'COURSE_NAME'






