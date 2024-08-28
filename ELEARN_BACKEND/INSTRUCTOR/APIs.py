from rest_framework import generics, status
from rest_framework.decorators import api_view
from HOME_AREA.models import COURSES
from rest_framework.response import Response
from rest_framework import routers, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from .Serializers import *
from django.shortcuts import get_object_or_404
from .models import *
from random import randint
from HOME_AREA.tasks import send_email
from STUDENT.models import STUDENT
from ELEARN_BACKEND.CUSTOME_DECORATOR import user_type_required
from django.contrib.auth.mixins import UserPassesTestMixin
# to ensure that only instructors can work with thsese APIs
class IsInstructor(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.user_cat =="instructor"
    def handle_no_permission(self):
        raise("not a valid user")
#instructor class to get a instructor(dashboard courses), delete instructor, update his data
class InstructorAPI(IsInstructor, mixins.CreateModelMixin, mixins.RetrieveModelMixin, 
                mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                 generics.GenericAPIView):
                queryset = INSTRUCTOR.objects.all()
                serializer_class = InstructorSerializer
                lookup_field = 'USER_NAME'
                #enforcing permissions from backend regardless of frontend
                def get_object(self):
                    obj = super().get_object()
                    if isinstance(self.request.user, AnonymousUser) or obj.USER_NAME != self.request.user.USER_NAME  :
                        raise PermissionDenied("You are not allowed to access this resource.")
                    return obj

                def get(self, request, *args , **kwargs):
                    return self.retrieve(request, *args, **kwargs)
                def put(self, request, *args, **kwargs):
                    return self.update(request, *args, **kwargs)
                def delete(self, request, *args, **kwargs):
                    return self.destroy(request, *args, **kwargs)
# course CRUD operation that instructor can create, edit, delete ,get his courses
class CourseCRUDAPI(IsInstructor, mixins.CreateModelMixin, mixins.RetrieveModelMixin, 
                mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                 generics.GenericAPIView):
                serializer_class = CoursCRUDAPISerializer
                #over kill already verified by IsInstructor class hahah 
                def get_object(self):
                    obj = super().get_object()

                    if isinstance(self.request.user, AnonymousUser) or obj.USER_NAME != self.request.user.USER_NAME  :
                        raise PermissionDenied("You are not allowed to access this resource.")
                    return obj
                
                def get_queryset(self):
                    courses = COURSES.objects.filter(
                    instructor__USER_NAME = request.user.USER_NAME
                    )
                # to ensure that instructor is saved(no mixing among instructors)
                def perform_create(self, serializer):
                    serializer.save(instructor=self.request.user)
                    return courses
                def post(self, request, *args , **kwargs):
                    return self.create(request, *args, **kwargs)
                def put(self, request, *args, **kwargs):
                    return self.update(request, *args, **kwargs)
                def delete(self, request, *args, **kwargs):
                    return self.destroy(request, *args, **kwargs)
                def get(self, request, *args , **kwargs):
                    return self.retrieve(request, *args, **kwargs)
# CRUD operations for lectures ensuring same origin
class LecturesCRUDsAPI(IsInstructor, mixins.CreateModelMixin, mixins.RetrieveModelMixin, 
                mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                 generics.GenericAPIView):

                serializer_class = LecturesCRUDserializer
                lookup_field = 'course__COURSE_NAME'
                def get_object(self):
                    obj = super().get_object()

                    if isinstance(self.request.user, AnonymousUser) or obj.USER_NAME != self.request.user.USER_NAME  :
                        raise PermissionDenied("You are not allowed to access this resource.")
                    return obj                
                def get_queryset(self):
                    courseName = self.kwargs.get(self.lookup_field)
                    lectures =LECTURES.objects.filter(course__COURSE_NAME = courseName)
                    return lectures

                def post(self, request, *args , **kwargs):
                    return self.create(request, *args, **kwargs)
                def put(self, request, *args, **kwargs):
                    return self.update(request, *args, **kwargs)
                def delete(self, request, *args, **kwargs):
                    return self.destroy(request, *args, **kwargs)
                def get(self, request, *args , **kwargs):
                    return self.retrieve(request, *args, **kwargs)
@api_view(["POST"])
def UNBlockHandlerAPI(request):
    if request.method == 'POST':
        serialized = BlockHandlerSerializer(data = request.data)
        if serialized.is_valid():
            cd = serialized.validated_data # student username 
            try:
                # if student is blocked remove him from blocklist of this instructor
                blocked = BLOCK_LIST.objects.get(students__USER_NAME = cd['USER_NAME'],
                                  instructors__USER_NAME = request.user.USER_NAME)
                blocked.delete()
                return Response({"message":"student removed from block list"}, status=status.HTTP_200_OK)
            except:
                return Respond({'message':"not  blocked"}, status=status.HTTP_404_NOT_FOUND) 
    return  Respond({'message':"SOMETHING WRONG HAPPENED"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def BlookHandlerAPI(request):
    if request.method == 'POST':
        serialized = BlockHandlerSerializer(data = request.data)
        if serialized.is_valid():
            cd = serialized.validated_data # student username 
            try:
                student = STUDENT.objects.get(USER_NAME = cd["USER_NAME"])  
                instr = INSTRUCTOR.objects.get(USER_NAME = request.user.USER_NAME)              
                blocked, created= BLOCK_LIST.objects.get_or_create(students = student,
                                  instructors = instr)
                if created:
                    return Response({"message": "Student added to block list"}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Student is already in the block list"}, status=status.HTTP_200_OK)
            
            except STUDENT.DoesNotExist:
                return Response({'message': "Student not found"}, status=status.HTTP_404_NOT_FOUND)
            except INSTRUCTOR.DoesNotExist:
                return Response({'message': "Instructor not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'message': f"Something went wrong: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({'message': "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)
