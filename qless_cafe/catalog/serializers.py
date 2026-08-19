from django.utils.text import slugify
from rest_framework import serializers

from .models import Category
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all(),
    )
    # Managers create/edit items by name, not slug — generate one when it's missing.
    slug = serializers.SlugField(required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "slug",
            "description",
            "price",
            "image",
            "is_available",
            "modifier_groups",
        ]

    def validate(self, attrs):
        if self.instance is None and not attrs.get("slug"):
            base = slugify(attrs.get("name", "")) or "item"
            slug = base
            suffix = 1
            while Product.objects.filter(slug=slug).exists():
                suffix += 1
                slug = f"{base}-{suffix}"
            attrs["slug"] = slug
        return attrs


class CategorySerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "tint", "display_order", "products"]

    def get_products(self, category):
        request = self.context.get("request")
        queryset = category.products.all()
        if not (request and request.user.is_authenticated and request.user.is_staff):
            queryset = queryset.filter(is_available=True)
        return ProductSerializer(queryset, many=True, context=self.context).data
