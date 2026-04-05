"""Сообщения чата по объекту: сохранение и уведомления сторонам."""

from django.contrib.auth import get_user_model

from .models import Notification, Property, PropertyChatMessage

User = get_user_model()


def user_can_access_property_chat(user, prop: Property) -> bool:
    """Риэлтор-владелец; клиент — по активному объекту в каталоге (первое сообщение с витрины без избранного)."""
    if not user.is_authenticated:
        return False
    if hasattr(user, "realtor_profile") and prop.realtor_id == user.realtor_profile.id:
        return True
    if not hasattr(user, "client_profile"):
        return False
    if prop.status in ("sold", "archived"):
        return False
    return True


def process_listing_chat_message(property_id: int, user: User, body: str) -> PropertyChatMessage:
    """
    Создаёт запись чата и шлёт уведомление контрагенту:
    клиент → риэлтору; риэлтор → всем клиентам, которые писали по объекту.
    """
    text = (body or "").strip()
    if not text or len(text) > 2000:
        raise ValueError("Пустое или слишком длинное сообщение.")

    prop = Property.objects.select_related("realtor", "realtor__user", "city").get(pk=property_id)
    msg = PropertyChatMessage.objects.create(property=prop, sender=user, body=text)

    is_owner = (
        hasattr(user, "realtor_profile")
        and prop.realtor_id
        and prop.realtor_id == user.realtor_profile.id
    )

    if is_owner:
        client_ids = (
            PropertyChatMessage.objects.filter(property=prop)
            .exclude(sender_id=user.id)
            .values_list("sender_id", flat=True)
            .distinct()
        )
        for uid in client_ids:
            try:
                u = User.objects.get(pk=uid)
            except User.DoesNotExist:
                continue
            if not hasattr(u, "client_profile"):
                continue
            Notification.objects.create(
                user=u,
                kind=Notification.Kind.CHAT_MESSAGE,
                title=f"Ответ риэлтора по объекту «{prop.title}»",
                body=text[:900],
                related_property=prop,
            )
    else:
        if prop.realtor_id:
            ru = prop.realtor.user
            who = (user.get_full_name() or "").strip() or user.username
            Notification.objects.create(
                user=ru,
                kind=Notification.Kind.CHAT_MESSAGE,
                title=f"Сообщение в чате: {prop.title}",
                body=f"{who}: {text[:800]}",
                related_property=prop,
            )

    return msg


def broadcast_listing_chat_message(property_id: int, payload: dict) -> None:
    """Уведомить открытые WebSocket-клиенты в комнате объекта (после POST из кабинета)."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            f"listing_chat_{property_id}",
            {"type": "chat_message", **payload},
        )
    except Exception:
        pass
