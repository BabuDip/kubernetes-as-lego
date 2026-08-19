from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.response import Response

from .models import Category
from .models import Product
from .modifiers import MODIFIER_GROUPS
from .serializers import CategorySerializer
from .serializers import ProductSerializer


class IsManagerOrReadOnly(permissions.BasePermission):
    """Anyone can read the catalogue; only cafe managers (is_staff) can write to it."""

    def has_permission(self, request, view) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and request.user.is_authenticated and request.user.is_staff,
        )


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManagerOrReadOnly]
    serializer_class = CategorySerializer
    queryset = Category.objects.prefetch_related("products")


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManagerOrReadOnly]
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = Product.objects.select_related("category")
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(is_available=True)
        return qs


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def modifier_groups(request):
    """Read-only: option labels/prices per group, matching Product.modifier_groups."""
    return Response(MODIFIER_GROUPS)
