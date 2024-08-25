from django.urls import path, re_path
from .consumers import *
websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>[\w\s-]+)/$", ChatConsumer.as_asgi()),
]