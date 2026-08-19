from __future__ import annotations

import pytest

from qless_cafe.catalog.tests.factories import CategoryFactory
from qless_cafe.catalog.tests.factories import ProductFactory

pytestmark = pytest.mark.django_db


def test_category_str():
    category = CategoryFactory(name="Coffee")
    assert str(category) == "Coffee"


def test_product_str():
    product = ProductFactory(name="Latte", slug="latte")
    assert str(product) == "Latte"


def test_category_ordering_by_display_order():
    second = CategoryFactory(name="Bakery", display_order=2)
    first = CategoryFactory(name="Coffee", display_order=1)
    assert list(type(first).objects.all()) == [first, second]
