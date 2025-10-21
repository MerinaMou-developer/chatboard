from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, pagination
from rest_framework.exceptions import PermissionDenied
from rooms.models import Room, RoomMember
from messages_app.models import Message
from .serializers import MessageSerializer

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

    def perform_create(self, serializer):
        room = get_object_or_404(Room, pk=self.kwargs["room_id"])
        # Must be a member to post
        if not RoomMember.objects.filter(room=room, user=self.request.user).exists():
            raise PermissionDenied("You are not a member of this room.")
        msg = serializer.save(sender=self.request.user, room=room, org=room.org)

        # fanout over WS: group name is "room:{id}"
        layer = get_channel_layer()
        payload = {
            "id": msg.id,
            "room": msg.room_id,
            "sender": msg.sender_id,
            "body": msg.body,
            "file_url": msg.file_url,
            "created_at": msg.created_at.isoformat(),
            "type": "message",
        }
        async_to_sync(layer.group_send)(f"room:{room.id}", {"type": "fanout", "payload": payload})
