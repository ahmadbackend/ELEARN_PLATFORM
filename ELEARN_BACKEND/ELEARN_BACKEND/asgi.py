"""
ASGI config for ELEARN_BACKEND project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from HOME_AREA.routing import ASGI_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ELEARN_BACKEND.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket':URLRouter(ASGI_urlpatterns)
})
