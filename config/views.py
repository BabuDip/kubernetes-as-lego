"""Views that don't belong to any particular app under qless_cafe/."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import JsonResponse
from django.views.decorators.http import require_GET

if TYPE_CHECKING:
    from django.http import HttpRequest


@require_GET
def healthcheck(request: HttpRequest) -> JsonResponse:
    """Liveness/readiness endpoint for kubelet and the GKE load balancer.

    Deliberately checks nothing else (no DB/Redis) — a liveness probe that
    depends on a downstream service causes cascading pod restarts whenever
    that service blips. See config.settings.production's SECURE_REDIRECT_EXEMPT:
    kubelet and the GCE health check both hit this path directly over plain
    HTTP (no X-Forwarded-Proto), so it's explicitly exempted from
    SECURE_SSL_REDIRECT rather than disabling that redirect globally.
    """
    return JsonResponse({"status": "ok"})
