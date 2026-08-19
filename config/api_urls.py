from django.urls import include
from django.urls import path

urlpatterns = [
    path("auth/", include("qless_cafe.identity.api_urls")),
    path("", include("qless_cafe.catalog.api_urls")),
    path("", include("qless_cafe.orders.api_urls")),
]
