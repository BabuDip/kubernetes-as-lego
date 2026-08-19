from rest_framework import serializers

from qless_cafe.catalog.models import Product

from .models import Order
from .models import OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "unit_price",
            "quantity",
            "modifiers_label",
            "subtotal",
        ]
        read_only_fields = ["product_name", "unit_price", "modifiers_label", "subtotal"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "display_id",
            "status",
            "status_steps",
            "pickup_preference",
            "note",
            "total",
            "ahead_count",
            "age_seconds",
            "age_display",
            "age_level",
            "created_at",
            "updated_at",
            "customer_name",
            "items",
        ]
        read_only_fields = [f for f in fields if f not in {"pickup_preference", "note"}]


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=20)
    # {group_key: option_id}, e.g. {"milk": "oat", "size": "lg"} — priced server-side.
    modifiers = serializers.DictField(
        child=serializers.CharField(),
        required=False,
        default=dict,
    )


class CreateOrderSerializer(serializers.Serializer):
    """What the checkout screen posts: cart lines + pickup preference + a note."""

    items = OrderItemInputSerializer(many=True, allow_empty=False)
    pickup_preference = serializers.ChoiceField(
        choices=Order.Pickup.choices,
        default=Order.Pickup.ASAP,
    )
    note = serializers.CharField(
        max_length=255,
        allow_blank=True,
        required=False,
        default="",
    )

    def validate_items(self, value):
        product_ids = [line["product_id"] for line in value]
        available = set(
            Product.objects.filter(id__in=product_ids, is_available=True).values_list(
                "id",
                flat=True,
            ),
        )
        missing = [str(pid) for pid in product_ids if pid not in available]
        if missing:
            msg = f"Product(s) no longer available: {', '.join(missing)}"
            raise serializers.ValidationError(msg)
        return value


class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
