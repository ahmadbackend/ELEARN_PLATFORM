#student class to get a student(dashboard), post a student(register new), delete student, update his data
# function to log in , verify , forget password
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import routers, status, mixins
from .serializers import *
from .models import *
from ELEARN_BACKEND.CUSTOME_DECORATOR import user_type_required

class StudentApi(mixins.CreateModelMixin, mixins.RetrieveModelMixin, 
                mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                 generics.GenericAPIView):
                queryset = STUDENT.objects.all()
                serializer_class = StudentSerializer
                def post(self, request, *args, **kwargs):
                    return self.create(request, *args, **kwargs)
                def get(self, request, *args , **kwargs):
                    return self.retrieve(request, *args, **kwargs)
                def put(self, request, *args, **kwargs):
                    return self.put(request, *args, **kwargs)
                def delete(self, request, *args, **kwargs):
                    return self.destroy(request, *args, **kwargs)