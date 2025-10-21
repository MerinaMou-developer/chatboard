from django.conf import settings
from django.db import models
from orgs.models import Organization
from rooms.models import Room

User = settings.AUTH_USER_MODEL

class Message(models.Model):
    org = models.ForeignKey(
        Organization, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="messages"
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    body = models.TextField(blank=True, default="")
    file_url = models.URLField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Optimized for: WHERE room_id = ? AND id < ?
        indexes = [
            models.Index(fields=["room", "-id"], name="msg_room_id_desc"),
            # keep this only if you need time-based queries:
            # models.Index(fields=["created_at"], name="msg_created_at_idx"),
        ]
        ordering = ["-id"]  # aligns with your API (newest first)

    def __str__(self):
        return f"Msg#{self.pk} room={self.room_id} sender={self.sender_id}"
