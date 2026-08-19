from django.urls import path
from rest_framework.routers import DefaultRouter

from .api_views import CategoryViewSet
from .api_views import ProductViewSet
from .api_views import modifier_groups

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")

urlpatterns = [
    path("modifier-groups/", modifier_groups, name="modifier-groups"),
    *router.urls,
]
