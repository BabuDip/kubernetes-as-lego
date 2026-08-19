from __future__ import annotations

import factory
from factory.django import DjangoModelFactory

from qless_cafe.catalog.tests.factories import ProductFactory
from qless_cafe.identity.tests.factories import UserFactory
from qless_cafe.orders.models import Order
from qless_cafe.orders.models import OrderItem


class OrderFactory(DjangoModelFactory[Order]):
    customer = factory.SubFactory(UserFactory)

    class Meta:
        model = Order


class OrderItemFactory(DjangoModelFactory[OrderItem]):
    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    product_name = "Latte"
    unit_price = "4.50"
    quantity = 1

    class Meta:
        model = OrderItem
