from __future__ import annotations

import uuid

import pytest

from qless_cafe.identity.tests.factories import UserFactory
from qless_cafe.orders.tasks import send_order_receipt_email
from qless_cafe.orders.tests.factories import OrderFactory
from qless_cafe.orders.tests.factories import OrderItemFactory

# transaction=True + a real worker thread: the task runs on its own DB connection,
# so it must see committed data rather than the test's (rolled-back) transaction.
pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.usefixtures("celery_session_worker"),
]


class TestSendOrderReceiptEmail:
    def test_sends_receipt_with_order_details(self, mailoutbox):
        customer = UserFactory(email="customer@example.com", name="Alex Rivera")
        order = OrderFactory(
            customer=customer,
            pickup_preference="in_10",
            note="No sugar",
        )
        OrderItemFactory(
            order=order,
            product_name="Flat White",
            unit_price="4.50",
            quantity=2,
        )

        # Dispatched through the real in-memory broker and executed by a live worker —
        # not called directly as a Python function.
        send_order_receipt_email.apply_async(args=(str(order.id),)).get(timeout=10)

        assert len(mailoutbox) == 1
        message = mailoutbox[0]
        assert message.to == ["customer@example.com"]
        assert order.display_id in message.subject
        html_body = message.alternatives[0][0]
        assert "Alex Rivera" in html_body
        assert "Flat White" in html_body
        assert "In 10 min" in html_body

    def test_skips_silently_when_order_missing(self, mailoutbox):
        send_order_receipt_email.apply_async(args=(str(uuid.uuid7()),)).get(timeout=10)

        assert len(mailoutbox) == 0
