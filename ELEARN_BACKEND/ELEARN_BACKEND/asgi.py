"""
ASGI config for ELEARN_BACKEND project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ELEARN_BACKEND.settings')
django_asgi_app = get_asgi_application()

# imported after django is set up because they touch the models
from HOME_AREA.routing import websocket_urlpatterns  # noqa: E402
from HOME_AREA.authentication import TokenAuthMiddleware  # noqa: E402

application = ProtocolTypeRouter({
    'http':  django_asgi_app,
    # session login (MVT pages) or `?token=<api token>` (SPA) both authenticate a socket
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(TokenAuthMiddleware(URLRouter(websocket_urlpatterns)))
    ),
})
