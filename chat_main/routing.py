from django.urls import re_path
from . import consumers
from .rag_consumer import CreatorRagConsumer

websocket_urlpatterns = [
    re_path(r'ws/channel/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/rag/(?P<channel_name>[^/]+)/$', CreatorRagConsumer.as_asgi()),
]