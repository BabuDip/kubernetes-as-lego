from __future__ import annotations

from decimal import Decimal

import pytest

from qless_cafe.orders.tests.factories import OrderFactory
from qless_cafe.orders.tests.factories import OrderItemFactory

pytestmark = pytest.mark.django_db


def test_order_number_is_sequential_and_human_readable():
    first = OrderFactory()
    second = OrderFactory()
    assert second.order_number == first.order_number + 1
    assert first.display_id == f"PO-{first.order_number:04d}"


def test_order_total_sums_item_subtotals():
    order = OrderFactory()
    OrderItemFactory(order=order, unit_price="4.50", quantity=2)
    OrderItemFactory(order=order, unit_price="3.00", quantity=1)
    assert order.total == Decimal("12.00")


def test_order_total_is_zero_with_no_items():
    order = OrderFactory()
    assert order.total == Decimal("0.00")
