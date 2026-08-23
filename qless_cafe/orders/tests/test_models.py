from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import connection

from qless_cafe.orders.models import _next_order_number
from qless_cafe.orders.tests.factories import OrderFactory
from qless_cafe.orders.tests.factories import OrderItemFactory

pytestmark = pytest.mark.django_db


def test_order_number_is_sequential_and_human_readable():
    first = OrderFactory()
    second = OrderFactory()
    assert second.order_number == first.order_number + 1
    assert first.display_id == f"PO-{first.order_number:04d}"


def test_next_order_number_falls_back_to_max_plus_one_off_postgresql(monkeypatch):
    # CI only runs against Postgres, so force the non-Postgres branch (the one
    # bare-local/SQLite runs actually use) to exercise it here too.
    monkeypatch.setattr(connection, "vendor", "sqlite")
    OrderFactory(order_number=5)
    assert _next_order_number() == 6  # noqa: PLR2004


def test_next_order_number_starts_at_one_off_postgresql_with_no_orders(monkeypatch):
    monkeypatch.setattr(connection, "vendor", "sqlite")
    assert _next_order_number() == 1


def test_order_total_sums_item_subtotals():
    order = OrderFactory()
    OrderItemFactory(order=order, unit_price="4.50", quantity=2)
    OrderItemFactory(order=order, unit_price="3.00", quantity=1)
    assert order.total == Decimal("12.00")


def test_order_total_is_zero_with_no_items():
    order = OrderFactory()
    assert order.total == Decimal("0.00")
