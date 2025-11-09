import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer, InvalidChannelLayerError
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, pagination, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rooms.models import Room, RoomMember
from notifications.models import Notification
from messages_app.models import Message
from .serializers import MessageSerializer

logger = logging.getLogger(__name__)

class DefaultPagination(pagination.PageNumberPagination):
    page_size = 50
    page_size_query_param = "limit"

class RoomMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        # Must be a member
        is_member = RoomMember.objects.filter(room_id=room_id, user=self.request.user).exists()
        if not is_member:
            raise PermissionDenied("You are not a member of this room.")
        qs = Message.objects.filter(room_id=room_id).select_related("sender").order_by("-id")
        # cursor-ish backward pagination via ?before=<id>
        before = self.request.query_params.get("before")
        if before:
            qs = qs.filter(id__lt=before)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room = get_object_or_404(Room, pk=self.kwargs["room_id"])
        if not RoomMember.objects.filter(room=room, user=request.user).exists():
            raise PermissionDenied("You are not a member of this room.")

        msg = serializer.save(sender=request.user, room=room, org=room.org)
        self._fanout(room, msg)
        self._notify_room_members(room, msg)

        output = self.get_serializer(instance=msg)
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    def _fanout(self, room, msg):
        try:
            layer = get_channel_layer()
        except InvalidChannelLayerError:
            logger.warning("Channel layer invalid; skipping fanout for message %s", msg.id)
            return
        except Exception:
            logger.exception("Unexpected error retrieving channel layer; skipping fanout for message %s", msg.id)
            return

        if not layer:
            logger.warning("Channel layer unavailable; skipping fanout for message %s", msg.id)
            return

        payload = {
            "id": msg.id,
            "room": msg.room_id,
            "sender": msg.sender_id,
            "body": msg.body,
            "file_url": msg.file_url,
            "created_at": msg.created_at.isoformat(),
            "type": "message",
        }

        group_name = f"room_{room.id}"

        try:
            async_to_sync(layer.group_send)(group_name, {"type": "fanout", "payload": payload})
        except Exception:
            logger.exception("Failed to broadcast message %s to room %s", msg.id, room.id)

    def _notify_room_members(self, room, msg):
        """Create notifications for everyone in the room except the sender."""
        member_ids = (
            RoomMember.objects.filter(room=room)
            .exclude(user=msg.sender)
            .values_list("user_id", flat=True)
        )

        if not member_ids:
            return

        if msg.body:
            preview = msg.body[:80]
            if len(msg.body) > 80:
                preview += "..."
        elif msg.file_url:
            preview = "shared a file"
        else:
            preview = "sent a message"

        sender_identifier = getattr(msg.sender, "email", None) or getattr(msg.sender, "username", None) or "Someone"

        notifications = [
            Notification(
                user_id=user_id,
                title=f"New message in {room.name}",
                message=f"{sender_identifier} {preview}",
                notification_type="message",
            )
            for user_id in member_ids
        ]

        Notification.objects.bulk_create(notifications, ignore_conflicts=True)
