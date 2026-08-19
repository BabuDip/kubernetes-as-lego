from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from http import HTTPStatus
from unittest.mock import patch

import pytest

from qless_cafe.catalog.tests.factories import ProductFactory
from qless_cafe.identity.tests.factories import UserFactory
from qless_cafe.orders.models import Order
from qless_cafe.orders.tests.factories import OrderFactory
from qless_cafe.orders.tests.factories import OrderItemFactory

pytestmark = pytest.mark.django_db


class TestCheckout:
    def test_creates_order_with_snapshot_pricing(self, client):
        client.force_login(UserFactory())
        product = ProductFactory(price="4.50")

        response = client.post(
            "/api/orders/",
            data={
                "items": [{"product_id": str(product.id), "quantity": 2}],
                "pickup_preference": "asap",
                "note": "no sugar",
            },
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.CREATED
        order = Order.objects.get()
        assert order.items.count() == 1
        assert order.total == Decimal("9.00")
        assert order.note == "no sugar"
        assert response.json()["display_id"] == order.display_id

    @patch("qless_cafe.orders.api_views.notify_managers")
    def test_checkout_notifies_managers(
        self,
        mock_notify_managers,
        client,
        django_capture_on_commit_callbacks,
    ):
        client.force_login(UserFactory())
        product = ProductFactory()

        with django_capture_on_commit_callbacks(execute=True):
            client.post(
                "/api/orders/",
                data={"items": [{"product_id": str(product.id), "quantity": 1}]},
                content_type="application/json",
            )

        mock_notify_managers.assert_called_once()
        assert mock_notify_managers.call_args[0][0] == "order.created"

    @patch("qless_cafe.orders.api_views.send_order_receipt_email")
    def test_checkout_queues_receipt_email(
        self,
        mock_send_receipt,
        client,
        django_capture_on_commit_callbacks,
    ):
        client.force_login(UserFactory())
        product = ProductFactory()

        with django_capture_on_commit_callbacks(execute=True):
            client.post(
                "/api/orders/",
                data={"items": [{"product_id": str(product.id), "quantity": 1}]},
                content_type="application/json",
            )

        order = Order.objects.get()
        mock_send_receipt.delay.assert_called_once_with(str(order.id))

    def test_rejects_unavailable_product(self, client):
        client.force_login(UserFactory())
        product = ProductFactory(is_available=False)

        response = client.post(
            "/api/orders/",
            data={"items": [{"product_id": str(product.id), "quantity": 1}]},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert not Order.objects.exists()

    def test_prices_and_labels_modifiers_server_side(self, client):
        """The server, not the client, decides the price — this is a trust boundary."""
        client.force_login(UserFactory())
        product = ProductFactory(price="4.50", modifier_groups=["milk", "size"])

        response = client.post(
            "/api/orders/",
            data={
                "items": [
                    {
                        "product_id": str(product.id),
                        "quantity": 1,
                        "modifiers": {"milk": "oat", "size": "lg"},
                    },
                ],
            },
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.CREATED
        item = Order.objects.get().items.get()
        assert item.unit_price == Decimal("6.00")  # 4.50 + 0.70 (oat) + 0.80 (large)
        assert item.modifiers_label == "Oat · Large"

    def test_rejects_invalid_modifier_option(self, client):
        client.force_login(UserFactory())
        product = ProductFactory(modifier_groups=["milk"])

        response = client.post(
            "/api/orders/",
            data={
                "items": [
                    {
                        "product_id": str(product.id),
                        "quantity": 1,
                        "modifiers": {"milk": "soy"},
                    },
                ],
            },
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert not Order.objects.exists()

    def test_requires_login(self, client):
        product = ProductFactory()
        response = client.post(
            "/api/orders/",
            data={"items": [{"product_id": str(product.id), "quantity": 1}]},
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestOrderOwnership:
    def test_customer_only_sees_their_own_orders(self, client):
        me = UserFactory()
        mine = OrderFactory(customer=me)
        OrderFactory(customer=UserFactory())

        client.force_login(me)
        response = client.get("/api/orders/")

        ids = {o["id"] for o in response.json()}
        assert ids == {str(mine.id)}

    def test_cannot_view_someone_elses_order(self, client):
        me = UserFactory()
        other_order = OrderFactory(customer=UserFactory())

        client.force_login(me)
        response = client.get(f"/api/orders/{other_order.id}/")

        assert response.status_code == HTTPStatus.NOT_FOUND


class TestManagerOrderWorkflow:
    def test_non_staff_cannot_advance_orders(self, client):
        order = OrderFactory()
        client.force_login(UserFactory(is_staff=False))

        response = client.post(
            f"/api/orders/{order.id}/advance/",
            data={},
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.FORBIDDEN

    @patch("qless_cafe.orders.api_views.notify")
    def test_advance_moves_status_and_notifies_customer(
        self,
        mock_notify,
        client,
        django_capture_on_commit_callbacks,
    ):
        order = OrderFactory(status=Order.Status.RECEIVED)
        OrderItemFactory(order=order)
        client.force_login(UserFactory(is_staff=True))

        with django_capture_on_commit_callbacks(execute=True):
            response = client.post(
                f"/api/orders/{order.id}/advance/",
                data={},
                content_type="application/json",
            )

        order.refresh_from_db()
        assert response.status_code == HTTPStatus.OK
        assert order.status == Order.Status.PREPARING
        mock_notify.assert_called_once()
        args, _kwargs = mock_notify.call_args
        assert args[0] == order.customer_id
        assert args[1] == "order.status_changed"

    def test_board_groups_orders_by_status(self, client):
        OrderFactory(status=Order.Status.RECEIVED)
        OrderFactory(status=Order.Status.PREPARING)
        OrderFactory(status=Order.Status.COMPLETED)
        client.force_login(UserFactory(is_staff=True))

        response = client.get("/api/orders/board/")

        data = response.json()
        assert len(data["received"]) == 1
        assert len(data["preparing"]) == 1
        assert len(data["completed"]) == 1

    def test_board_completed_column_excludes_older_days(self, client):
        yesterday = OrderFactory(status=Order.Status.COMPLETED)
        Order.objects.filter(pk=yesterday.pk).update(
            created_at=yesterday.created_at - timedelta(days=1),
        )
        client.force_login(UserFactory(is_staff=True))

        response = client.get("/api/orders/board/")

        assert response.json()["completed"] == []

    def test_stats_counts_todays_orders(self, client):
        OrderFactory(status=Order.Status.RECEIVED)
        OrderFactory(status=Order.Status.READY)
        client.force_login(UserFactory(is_staff=True))

        response = client.get("/api/orders/stats/")

        data = response.json()
        assert data["orders_today"] == 2  # noqa: PLR2004
        assert data["pending"] == 1
        assert data["ready"] == 1
        assert data["oldest_wait_seconds"] is not None

    def test_stats_oldest_wait_is_none_when_queue_empty(self, client):
        OrderFactory(status=Order.Status.COMPLETED)
        client.force_login(UserFactory(is_staff=True))

        response = client.get("/api/orders/stats/")

        assert response.json()["oldest_wait_seconds"] is None
