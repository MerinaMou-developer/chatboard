from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from notifications.models import Notification
from notifications.api.base.serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    """Manage user notifications."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user."""
        updated_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).update(
            is_read=True, 
            read_at=timezone.now()
        )
        
        return Response({
            'detail': f'Marked {updated_count} notifications as read'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        
        return Response({'unread_count': count})