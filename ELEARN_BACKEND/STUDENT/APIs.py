# function to log in , verify , forget password
from rest_framework import generics
from rest_framework.decorators import api_view
from HOME_AREA.models import COURSES
from rest_framework.response import Response
from rest_framework import routers, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from .serializers import *
from django.shortcuts import get_object_or_404
from .models import *
from ELEARN_BACKEND.CUSTOME_DECORATOR import user_type_required

#student class to get a student(dashboard courses), post a student(register new), delete student, update his data
class StudentApi(mixins.CreateModelMixin, mixins.RetrieveModelMixin, 
                mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                 generics.GenericAPIView):
                queryset = STUDENT.objects.all()
                serializer_class = StudentSerializer
                lookup_field = 'USER_NAME'
                #enforcing permissions from backend regardless of frontend
                def get_object(self):
                    obj = super().get_object()
                    if isinstance(self.request.user, AnonymousUser) or obj.USER_NAME != self.request.user.USER_NAME  :
                        raise PermissionDenied("You are not allowed to access this resource.")
                    return obj
                def post(self, request, *args, **kwargs):
                    return self.create(request, *args, **kwargs)
                def get(self, request, *args , **kwargs):
                    return self.retrieve(request, *args, **kwargs)
                def put(self, request, *args, **kwargs):
                    return self.update(request, *args, **kwargs)
                def delete(self, request, *args, **kwargs):
                    return self.destroy(request, *args, **kwargs)



#student can drop a course or get its details 
"""
#in return view you will see all enrolled courses but delete will 
execute only the queried course

"""
class COURSE_student_APIs(mixins.CreateModelMixin, mixins.RetrieveModelMixin, 
                mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                 generics.GenericAPIView):
                serializer_class = CourseStudentSerializer
                lookup_field = 'course__COURSE_NAME'
                def get_queryset(self):
                    # Retrieve the current logged-in student
                    stu = STUDENT.objects.get(USER_NAME=self.request.user.USER_NAME)
                    
                    # Retrieve the course name from the URL kwargs
                    course_name = self.kwargs.get(self.lookup_field)
                    cour = COURSES.objects.get(COURSE_NAME=course_name)
                    
                    # Filter the COURSE_LIST for this student and specific course
                    return COURSE_LIST.objects.filter(student=stu, course=cour)
                def get(self, request, *args , **kwargs):
                    return self.retrieve(request, *args, **kwargs)
                #drop the course    
                def delete(self, request, *args, **kwargs):
                    return self.destroy(request, *args, **kwargs)
