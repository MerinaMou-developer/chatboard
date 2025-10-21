from rest_framework import generics, permissions
from rest_framework.response import Response
from django.db.models import Count, Q
from rooms.models import RoomMember
from messages_app.models import Message
from .serializers import RegisterSerializer, MeSerializer

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user

class UnreadCountsView(generics.GenericAPIView):
    """Get unread message counts for all rooms the user is a member of."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get all rooms where user is a member
        room_memberships = RoomMember.objects.filter(user=request.user).select_related('room')
        
        unread_counts = []
        for membership in room_memberships:
            # Count messages newer than last_read_msg_id
            if membership.last_read_msg_id:
                unread_count = Message.objects.filter(
                    room=membership.room,
                    id__gt=membership.last_read_msg_id,
                    sender_id__ne=request.user.id  # Don't count own messages
                ).count()
            else:
                # If never read, count all messages except own
                unread_count = Message.objects.filter(
                    room=membership.room,
                    sender_id__ne=request.user.id
                ).count()
            
            unread_counts.append({
                'room_id': membership.room.id,
                'room_name': membership.room.name,
                'unread_count': unread_count
            })
        
        return Response({'unread_counts': unread_counts})
