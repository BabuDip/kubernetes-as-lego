import uuid
from datetime import UTC
from datetime import datetime
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def _send(group_name: str, event: str, payload: dict[str, Any]) -> None:
    envelope = {
        "type": event,
        "id": str(uuid.uuid4()),
        "ts": datetime.now(tz=UTC).isoformat(),
        "data": payload,
    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "notify_event", "envelope": envelope},
    )


def notify(user_id: uuid.UUID | str, event: str, payload: dict[str, Any]) -> None:
    """The only entry point for a user event; never call group_send directly."""
    _send(f"user.{user_id}", event, payload)


def notify_managers(event: str, payload: dict[str, Any]) -> None:
    """Push a real-time event to every connected staff member (see consumers.py)."""
    _send("managers", event, payload)
