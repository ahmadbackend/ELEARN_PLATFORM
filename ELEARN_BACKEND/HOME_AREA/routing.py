from django.urls import re_path

from .consumers import PeerChatConsumer

# the learner <-> tutor room is the only websocket the platform exposes; it is
# authenticated with the same JWT the REST API uses (?token=<jwt>)
websocket_urlpatterns = [
    re_path(r'ws/peerchat/(?P<instructor>[^/]+)/(?P<student>[^/]+)/$', PeerChatConsumer.as_asgi()),
]
