# function to log in , verify , forget password
from rest_framework import generics, status
from rest_framework.views import APIView
from HOME_AREA.models import COURSES

from rest_framework.response import Response
from rest_framework import routers, status, mixins
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from .serializers import *
from HOME_AREA.forms import * 
from django.shortcuts import get_object_or_404
from .models import *
from random import randint
from HOME_AREA.tasks import send_email
from ELEARN_BACKEND.CUSTOME_DECORATOR import user_type_required

#student class to get a student(dashboard courses), delete student, update his data
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
#look in the above comment please
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
                    #enrol in a course 
                def post(self, request, *args , **kwargs):
                    return self.create(request, *args, **kwargs)
                #drop the course    
                def delete(self, request, *args, **kwargs):
                    return self.destroy(request, *args, **kwargs)
#register and login student

class StudentReg(generics.CreateAPIView):
    serializer_class = StudentSerializer

    def create(self, request, *args, **kwargs):
        serialize = self.get_serializer(data =request.data)
        serialize.is_valid(raise_exception = True)
        self.perform_create(serialize)
        return Response({"message": "User created successfully but not activated yet"}, status=status.HTTP_201_CREATED)

class StudentLogAPI(APIView):
    serializer_class = LogInSerializerStudent

    def post(self, request):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            return Response({"message": "User logged in successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({'message': "INVALID INPUT"}, status=status.HTTP_404_NOT_FOUND)



class VerifyStudentAPI(APIView):
    serializer_class = VrifySerializer

    def post(self, request):
        serialized = self.serializer_class(data=request.data)
        if serialized.is_valid():
            try:
                data = serialized.validated_data
                verified = CODE_GENERATOR.objects.get(EMAIL=data['EMAIL'], ACTIVATION_CODE=data["ACTIVATION_CODE"])
                return Response({"message": "User verified"}, status=status.HTTP_200_OK)
            except CODE_GENERATOR.DoesNotExist:
                raise ValidationError("invalid input")
        else:
            return Response({'message': "INVALID INPUT"}, status=status.HTTP_404_NOT_FOUND)

class ForgetPassStudentAPI(APIView):
    serializer_class = ForgetPassSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                cd = serializer.validated_data
                student = STUDENT.objects.get(EMAIL=cd['EMAIL'])
                verification_code = randint(100000, 999999)
                message = f"this code was sent based on your request to restore the login credential. Ignore if you did not send it: {verification_code}"
                
                send_email(cd["EMAIL"], message)
                CODE_GENERATOR.objects.create(USER_VERIFIER=student, ACTIVATION_CODE=verification_code, EMAIL=cd["EMAIL"])
                return Response({'message': "code sent successfully"}, status=status.HTTP_202_ACCEPTED)
            except STUDENT.DoesNotExist:
                return Response({'message': "email not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response("INVALID INPUT", status=status.HTTP_400_BAD_REQUEST)
