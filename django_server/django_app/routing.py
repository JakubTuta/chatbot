from django.urls import re_path

from container import consumers as container_consumers

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<chat_id>\d+)/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/compare/$", consumers.CompareConsumer.as_asgi()),
    re_path(r"ws/containers/$", container_consumers.ContainerStatusConsumer.as_asgi()),
]
