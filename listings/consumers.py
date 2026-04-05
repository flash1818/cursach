import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from .chat_utils import process_listing_chat_message


@database_sync_to_async
def save_chat_message(property_id: int, user_id: int, text: str) -> dict:
    User = get_user_model()
    user = User.objects.get(pk=user_id)
    msg = process_listing_chat_message(property_id, user, text)
    return {
        "message": msg.body,
        "username": user.get_username(),
        "id": msg.id,
        "created_at": msg.created_at.isoformat(),
    }


class ListingChatConsumer(AsyncWebsocketConsumer):
    """Чат по объекту: сообщения сохраняются в БД и дублируются в уведомлениях."""

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.property_id = int(self.scope["url_route"]["kwargs"]["property_id"])
        self.group_name = f"listing_chat_{self.property_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        gn = getattr(self, "group_name", None)
        if gn:
            await self.channel_layer.group_discard(gn, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        message = (data.get("message") or "").strip()
        if not message or len(message) > 2000:
            return
        user = self.scope["user"]
        try:
            payload = await save_chat_message(self.property_id, user.id, message)
        except Exception:
            return
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                **payload,
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "username": event["username"],
                    "id": event.get("id"),
                    "created_at": event.get("created_at"),
                },
                ensure_ascii=False,
            )
        )
