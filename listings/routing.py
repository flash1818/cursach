from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/chat/<int:property_id>/", consumers.ListingChatConsumer.as_asgi()),
]
