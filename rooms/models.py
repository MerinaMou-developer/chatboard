from django.db import models

# Create your models here.
from django.conf import settings

from orgs.models import Organization

User = settings.AUTH_USER_MODEL

class Room(models.Model):
    PUBLIC, PRIVATE, MANAGER_ONLY = "PUBLIC", "PRIVATE", "MANAGER_ONLY"
    ACCESS_CHOICES = [
        (PUBLIC, "All org members"),
        (PRIVATE, "Invite only"),
        (MANAGER_ONLY, "Manager/Admin only")
    ]
    
    org = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name="rooms")
    name = models.CharField(max_length=120)
    is_dm = models.BooleanField(default=False)
    access_level = models.CharField(max_length=12, choices=ACCESS_CHOICES, default=PUBLIC)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_rooms")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-id"]

    def __str__(self):
        return self.name


class RoomMember(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="room_memberships")
    last_read_msg_id = models.BigIntegerField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["room", "user"], name="uniq_room_user")
        ]
        indexes = [
            models.Index(fields=["room", "user"]),
        ]
        ordering = ["-id"]

    def __str__(self):
        return f"{self.user_id}@{self.room_id}"
