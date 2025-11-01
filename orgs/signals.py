from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OrganizationMember


@receiver(post_save, sender=OrganizationMember)
def auto_join_public_rooms(sender, instance, created, **kwargs):
    """Automatically join new members to PUBLIC and MANAGER_ONLY rooms based on their role."""
    if created:  # Only when membership is first created
        org = instance.org
        user_role = instance.role
        
        # Import Room here to avoid circular imports
        from rooms.models import Room, RoomMember
        
        # Get all rooms in this organization
        rooms = Room.objects.filter(org=org)
        
        for room in rooms:
            # Determine if user should auto-join
            should_join = False
            if room.access_level == Room.PUBLIC:
                should_join = True  # All org members
            elif room.access_level == Room.MANAGER_ONLY:
                should_join = user_role in {"MANAGER", "ADMIN"}  # Only managers/admins
            
            if should_join:
                RoomMember.objects.get_or_create(room=room, user=instance.user)

