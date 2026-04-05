"""
ASGI config for realestate_site project.

HTTP — Django; WebSocket — Channels (чат по объекту). Запуск: daphne realestate_site.asgi:application

Важно: сначала задать DJANGO_SETTINGS_MODULE и вызвать get_asgi_application(), и только потом
импортировать listings.routing (иначе consumers → models поднимаются без настроек Django).
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "realestate_site.settings")

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import listings.routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(listings.routing.websocket_urlpatterns)),
    }
)
