from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import Order

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_receipt_email(self, order_id: str) -> None:
    """Email the customer a digital receipt (queued via transaction.on_commit)."""
    try:
        order = (
            Order.objects.select_related("customer")
            .prefetch_related("items")
            .get(pk=order_id)
        )
    except Order.DoesNotExist:
        logger.warning("send_order_receipt_email: order %s no longer exists", order_id)
        return

    context = {"order": order, "items": list(order.items.all())}
    html_body = render_to_string("emails/order_receipt.html", context)

    message = EmailMultiAlternatives(
        subject=f"Your receipt — {order.display_id} — QLess Cafe",
        body=strip_tags(html_body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.customer.email],
    )
    message.attach_alternative(html_body, "text/html")

    try:
        message.send()
    except Exception as exc:
        logger.exception(
            "send_order_receipt_email: failed to send for order %s",
            order_id,
        )
        raise self.retry(exc=exc) from exc
