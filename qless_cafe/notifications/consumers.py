from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Per-user notification stream. See notify() in services.py for the only way in."""

    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return
        self.group_name = f"user.{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        # Staff also get board-wide events (new orders, status changes) so the
        # Service Board updates live instead of relying on polling.
        self.staff_group_name = "managers" if user.is_staff else None
        if self.staff_group_name:
            await self.channel_layer.group_add(self.staff_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if getattr(self, "staff_group_name", None):
            await self.channel_layer.group_discard(
                self.staff_group_name,
                self.channel_name,
            )

    async def notify_event(self, message):
        """Handler name must match the "type" key sent via group_send in services.py."""
        await self.send_json(message["envelope"])
