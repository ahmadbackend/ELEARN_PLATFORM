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
from ELEARN_BACKEND.CUSTOME_DECORATOR import user_type_required

#instructor class to get a instructor(dashboard courses), delete instructor, update his data
class InstructorAPI(mixins.CreateModelMixin, mixins.RetrieveModelMixin, 
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
