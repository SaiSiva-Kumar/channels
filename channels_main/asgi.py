"""
ASGI config for channels_main project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'channels_main.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat_main import routing
from end_point_middleware.firebase_ws_auth import FirebaseAuthMiddleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": FirebaseAuthMiddleware(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})