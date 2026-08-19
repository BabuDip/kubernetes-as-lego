from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from typing import cast

from django.db import transaction
from django.utils import timezone
from rest_framework import permissions
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from qless_cafe.catalog.models import Product
from qless_cafe.catalog.modifiers import resolve_modifiers
from qless_cafe.notifications.services import notify
from qless_cafe.notifications.services import notify_managers

from .models import Order
from .models import OrderItem
from .serializers import CreateOrderSerializer
from .serializers import OrderSerializer
from .serializers import UpdateOrderStatusSerializer
from .tasks import send_order_receipt_email

if TYPE_CHECKING:
    from qless_cafe.identity.models import User

# What a manager taps next, and what that button says. Completed is a dead end.
NEXT_STATUS = {
    Order.Status.RECEIVED: Order.Status.PREPARING,
    Order.Status.PREPARING: Order.Status.READY,
    Order.Status.READY: Order.Status.COMPLETED,
}


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user and request.user.is_authenticated and request.user.is_staff,
        )


class OrderViewSet(viewsets.ModelViewSet):
    """Customers see + create their own orders; managers get the full queue/actions."""

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user = cast("User", self.request.user)
        qs = Order.objects.select_related("customer").prefetch_related("items")
        if user.is_staff:
            return qs
        return qs.filter(customer=user)

    def get_permissions(self):
        if self.action in {"advance", "stats", "board"}:
            return [permissions.IsAuthenticated(), IsManager()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lines = serializer.validated_data["items"]
        products = {
            p.id: p
            for p in Product.objects.filter(
                id__in=[line["product_id"] for line in lines],
            )
        }

        try:
            priced_lines = [
                (
                    products[line["product_id"]],
                    line["quantity"],
                    *resolve_modifiers(
                        products[line["product_id"]].modifier_groups,
                        line.get("modifiers", {}),
                    ),
                )
                for line in lines
            ]
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        with transaction.atomic():
            order = Order.objects.create(
                customer=request.user,
                pickup_preference=serializer.validated_data["pickup_preference"],
                note=serializer.validated_data.get("note", ""),
            )
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        product=product,
                        product_name=product.name,
                        unit_price=product.price + extra,
                        quantity=quantity,
                        modifiers_label=label,
                    )
                    for product, quantity, extra, label in priced_lines
                ],
            )
            customer_name = request.user.name or request.user.email
            transaction.on_commit(
                lambda: notify_managers(
                    "order.created",
                    {
                        "order_id": str(order.id),
                        "message": (
                            f"New order {order.display_id} from {customer_name}."
                        ),
                    },
                ),
            )
            # Payment is simulated at checkout: this is the "payment received" moment,
            # so the receipt email is queued on the worker, never blocking the response.
            transaction.on_commit(
                lambda: send_order_receipt_email.delay(str(order.id)),
            )
        order.refresh_from_db()
        return Response(
            OrderSerializer(order).data,
            status=http_status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def advance(self, request, pk=None):
        order = self.get_object()
        serializer = UpdateOrderStatusSerializer(data=request.data or {})
        if request.data:
            serializer.is_valid(raise_exception=True)
            new_status = serializer.validated_data["status"]
        else:
            new_status = NEXT_STATUS.get(order.status)
        if new_status is None or new_status not in Order.Status.values:
            msg = "No valid next status for this order."
            raise PermissionDenied(msg)

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        transaction.on_commit(
            lambda: notify(
                order.customer_id,
                "order.status_changed",
                {
                    "order_id": str(order.id),
                    "status": order.status,
                    "message": f"Your order is now {order.get_status_display()}.",
                },
            ),
        )
        status_display = order.get_status_display()
        transaction.on_commit(
            lambda: notify_managers(
                "order.status_changed",
                {
                    "order_id": str(order.id),
                    "status": order.status,
                    "message": f"{order.display_id} is now {status_display}.",
                },
            ),
        )
        return Response(OrderSerializer(order).data)

    @action(detail=False, methods=["get"])
    def board(self, request):
        today = timezone.localdate()
        columns = {}
        for value, _label in Order.Status.choices:
            orders = (
                Order.objects.filter(status=value)
                .select_related("customer")
                .prefetch_related("items")
            )
            if value == Order.Status.COMPLETED:
                # Otherwise this column grows forever — just today's, most recent first.
                orders = orders.filter(created_at__date=today).order_by("-updated_at")
            else:
                orders = orders.order_by("created_at")
            columns[value] = OrderSerializer(orders, many=True).data
        return Response(columns)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        today = timezone.localdate()
        orders_today = Order.objects.filter(created_at__date=today)
        completed_today = orders_today.filter(status=Order.Status.COMPLETED)
        make_times = [
            (o.updated_at - o.created_at).total_seconds()
            for o in completed_today.only("created_at", "updated_at")
        ]
        avg_make_seconds = int(sum(make_times) / len(make_times)) if make_times else 0
        oldest_active = (
            Order.objects.filter(
                status__in=[Order.Status.RECEIVED, Order.Status.PREPARING],
            )
            .order_by("created_at")
            .first()
        )
        return Response(
            {
                "orders_today": orders_today.count(),
                "taken_today": completed_today.count(),
                "pending": Order.objects.filter(
                    status__in=[Order.Status.RECEIVED, Order.Status.PREPARING],
                ).count(),
                "ready": Order.objects.filter(status=Order.Status.READY).count(),
                "oldest_wait_seconds": oldest_active.age_seconds
                if oldest_active
                else None,
                "revenue_today": sum(
                    (o.total for o in completed_today),
                    Decimal("0.00"),
                ),
                "avg_make_seconds": avg_make_seconds,
            },
        )
