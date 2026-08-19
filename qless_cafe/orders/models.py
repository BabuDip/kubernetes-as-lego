import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models.expressions import RawSQL
from django.utils import timezone

from qless_cafe.catalog.models import Product

# Aging-bar thresholds (minutes) for Order.age_level.
_AGE_WARN_MINUTES = 4
_AGE_LATE_MINUTES = 8


class Order(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        COMPLETED = "completed", "Completed"

    class Pickup(models.TextChoices):
        ASAP = "asap", "ASAP"
        IN_10 = "in_10", "In 10 min"
        IN_20 = "in_20", "In 20 min"

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    # Sequential, human-readable order number for staff/customers to read out loud;
    # the UUID id above is for system/URL integrity only. Backed by a real Postgres
    # sequence (see migration) so concurrent checkouts never collide or race.
    order_number = models.PositiveIntegerField(
        unique=True,
        editable=False,
        db_default=RawSQL("nextval('orders_order_number_seq')", []),
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
    )
    pickup_preference = models.CharField(
        max_length=10,
        choices=Pickup.choices,
        default=Pickup.ASAP,
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order {self.display_id} ({self.customer})"

    @property
    def display_id(self) -> str:
        """Human-readable order number, e.g. "PO-0042"."""
        return f"PO-{self.order_number:04d}"

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items.all()), Decimal("0.00"))

    @property
    def ahead_count(self) -> int:
        """How many other active orders were placed before this one."""
        return (
            Order.objects.filter(
                status__in=[self.Status.RECEIVED, self.Status.PREPARING],
                created_at__lt=self.created_at,
            )
            .exclude(pk=self.pk)
            .count()
        )

    @property
    def age_seconds(self) -> int:
        end = (
            self.updated_at if self.status == self.Status.COMPLETED else timezone.now()
        )
        return max(0, int((end - self.created_at).total_seconds()))

    @property
    def age_display(self) -> str:
        """Elapsed time as "M:SS", for the Kanban card's wait pill."""
        minutes, seconds = divmod(self.age_seconds, 60)
        return f"{minutes}:{seconds:02d}"

    @property
    def age_level(self) -> str:
        """Aging-bar colour: pine (fresh) → crema (waiting) → brick (late)."""
        minutes = self.age_seconds / 60
        if minutes > _AGE_LATE_MINUTES:
            return "late"
        if minutes > _AGE_WARN_MINUTES:
            return "warn"
        return "ok"

    @property
    def status_steps(self) -> list[dict]:
        """Progress-stepper entries: value/label/state (done, current, or pending)."""
        values = [value for value, _label in self.Status.choices]
        current_index = values.index(self.status)
        steps = []
        for index, (value, label) in enumerate(self.Status.choices):
            if index < current_index:
                state = "done"
            elif index == current_index:
                state = "current"
            else:
                state = "pending"
            steps.append({"value": value, "label": label, "state": state})
        return steps


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    # Snapshot the name/price at order time so later catalogue edits don't rewrite
    # history.
    product_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=7, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    # Human-readable chosen options, e.g. "Oat · Large" — already priced into
    # unit_price.
    modifiers_label = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product_name}"

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity
