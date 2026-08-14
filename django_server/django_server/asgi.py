"""
ASGI config for django_server project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_server.settings")

# get_asgi_application() runs django.setup(), populating the app registry.
# It has to happen before django_app.routing is imported below — that import
# chain reaches into consumers -> functions -> models, which need the
# registry ready. This only worked before because `manage.py runserver`
# (which Channels transparently swaps for its own ASGI-aware command)
# bootstrapped Django ahead of time; invoking daphne directly against this
# module does not.
django_asgi_app = get_asgi_application()

import django_app.routing as app_routing  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            URLRouter(app_routing.websocket_urlpatterns)
        ),
    }
)
