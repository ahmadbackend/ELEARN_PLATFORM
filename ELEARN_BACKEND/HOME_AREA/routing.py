from django.urls import path
from . import consumer
ASGI_urlpatterns = [
    path('websocket', consumer.test.as_asgi())
]