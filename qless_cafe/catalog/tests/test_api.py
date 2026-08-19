from __future__ import annotations

from http import HTTPStatus

import pytest

from qless_cafe.catalog.tests.factories import CategoryFactory
from qless_cafe.catalog.tests.factories import ProductFactory
from qless_cafe.identity.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestCatalogueVisibility:
    def test_anonymous_sees_only_available_products(self, client):
        category = CategoryFactory(name="Coffee")
        ProductFactory(category=category, name="Latte", is_available=True)
        ProductFactory(category=category, name="Retired", is_available=False)

        response = client.get("/api/categories/")

        assert response.status_code == HTTPStatus.OK
        names = {p["name"] for c in response.json() for p in c["products"]}
        assert names == {"Latte"}

    def test_manager_sees_unavailable_products_too(self, client):
        category = CategoryFactory(name="Coffee")
        ProductFactory(category=category, name="Retired", is_available=False)
        client.force_login(UserFactory(is_staff=True))

        response = client.get("/api/categories/")

        names = {p["name"] for c in response.json() for p in c["products"]}
        assert "Retired" in names


class TestProductWriteAccess:
    def test_customer_cannot_toggle_availability(self, client):
        product = ProductFactory(is_available=True)
        client.force_login(UserFactory(is_staff=False))

        response = client.patch(
            f"/api/products/{product.id}/",
            data={"is_available": False},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        product.refresh_from_db()
        assert product.is_available is True

    def test_manager_can_toggle_availability(self, client):
        product = ProductFactory(is_available=True)
        client.force_login(UserFactory(is_staff=True))

        response = client.patch(
            f"/api/products/{product.id}/",
            data={"is_available": False},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.OK
        product.refresh_from_db()
        assert product.is_available is False

    def test_manager_can_create_product_with_auto_slug(self, client):
        CategoryFactory(slug="bakery")
        client.force_login(UserFactory(is_staff=True))

        response = client.post(
            "/api/products/",
            data={
                "category": "bakery",
                "name": "Ginger Slice",
                "description": "House-made, spiced.",
                "price": "5.20",
                "modifier_groups": ["heat"],
            },
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["slug"] == "ginger-slice"
        assert data["modifier_groups"] == ["heat"]

    def test_manager_can_edit_product_details_and_modifiers(self, client):
        product = ProductFactory(name="Latte", price="4.50", modifier_groups=[])
        client.force_login(UserFactory(is_staff=True))

        response = client.patch(
            f"/api/products/{product.id}/",
            data={"price": "5.00", "modifier_groups": ["milk", "size"]},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.OK
        product.refresh_from_db()
        assert str(product.price) == "5.00"
        assert product.modifier_groups == ["milk", "size"]

    def test_customer_cannot_create_product(self, client):
        category = CategoryFactory()
        client.force_login(UserFactory(is_staff=False))

        response = client.post(
            "/api/products/",
            data={"category": category.slug, "name": "Hack", "price": "1.00"},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
