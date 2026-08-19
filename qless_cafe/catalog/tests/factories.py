from __future__ import annotations

import factory
from factory.django import DjangoModelFactory

from qless_cafe.catalog.models import Category
from qless_cafe.catalog.models import Product


class CategoryFactory(DjangoModelFactory[Category]):
    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")
    icon = "cup-hot"

    class Meta:
        model = Category


class ProductFactory(DjangoModelFactory[Product]):
    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"Product {n}")
    slug = factory.Sequence(lambda n: f"product-{n}")
    description = "A tasty item."
    price = "4.50"
    is_available = True

    class Meta:
        model = Product
