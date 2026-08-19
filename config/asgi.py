"""
ASGI config for QLess Cafe project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/

"""

import os
import sys
from pathlib import Path

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter
from django.conf import settings
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.core.asgi import get_asgi_application
from django.views.static import serve as serve_media

# This allows easy placement of apps within the interior
# qless_cafe directory.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(BASE_DIR / "qless_cafe"))

# If DJANGO_SETTINGS_MODULE is unset, default to the local settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# Populates the app registry before anything below imports models.
django_asgi_app = get_asgi_application()

from qless_cafe.notifications.routing import websocket_urlpatterns  # noqa: E402


class ASGIMediaFilesHandler(ASGIStaticFilesHandler):
    """ASGIStaticFilesHandler for MEDIA_URL — Django only ships the STATIC_URL one.

    Reuses its request handling and, crucially, its get_response_async() fix-up that
    converts a sync StreamingHttpResponse into a real async generator up front, so
    Django's ASGI handler never has to fall back to consuming it synchronously.
    """

    def get_base_url(self):
        return settings.MEDIA_URL

    def serve(self, request):
        return serve_media(
            request,
            self.file_path(request.path),
            document_root=settings.MEDIA_ROOT,
        )


if settings.DEBUG:
    django_asgi_app = ASGIMediaFilesHandler(ASGIStaticFilesHandler(django_asgi_app))

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    },
)
