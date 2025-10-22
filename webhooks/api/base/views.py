from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from webhooks.models import Webhook, WebhookOutbox
from webhooks.api.base.serializers import WebhookSerializer, WebhookTestSerializer
from orgs.models import OrganizationMember
from config.permissions import IsOrgAdmin


class WebhookViewSet(viewsets.ModelViewSet):
    """Manage webhooks for organizations."""
    serializer_class = WebhookSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgAdmin]
    
    def get_queryset(self):
        # Only show webhooks for orgs where user is admin
        admin_org_ids = OrganizationMember.objects.filter(
            user=self.request.user, 
            role=OrganizationMember.ADMIN
        ).values_list('org_id', flat=True)
        return Webhook.objects.filter(org_id__in=admin_org_ids)
    
    def perform_create(self, serializer):
        org_id = serializer.validated_data['org'].id
        # Verify user is admin of this org
        if not OrganizationMember.objects.filter(
            org_id=org_id, 
            user=self.request.user, 
            role=OrganizationMember.ADMIN
        ).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only org admins can create webhooks.")
        serializer.save()
    
    @action(detail=True, methods=['post'], url_path='test')
    def test_webhook(self, request, pk=None):
        """Send a test webhook to verify configuration."""
        webhook = self.get_object()
        
        # Create test payload
        test_payload = {
            'event': 'webhook.test',
            'data': {
                'webhook_id': webhook.id,
                'org_id': webhook.org.id,
                'org_name': webhook.org.name,
                'timestamp': webhook.created_at.isoformat(),
                'message': 'This is a test webhook from ChatBoard'
            }
        }
        
        # Create outbox entry
        with transaction.atomic():
            outbox_entry = WebhookOutbox.objects.create(
                webhook=webhook,
                event_type='webhook.test',
                payload=test_payload
            )
        
        return Response({
            'detail': 'Test webhook queued for delivery',
            'outbox_id': outbox_entry.id,
            'webhook_url': webhook.url
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='events')
    def webhook_events(self, request, pk=None):
        """List recent webhook delivery attempts."""
        webhook = self.get_object()
        events = WebhookOutbox.objects.filter(webhook=webhook).order_by('-created_at')[:50]
        
        return Response([{
            'id': event.id,
            'event_type': event.event_type,
            'status': event.status,
            'retries': event.retries,
            'created_at': event.created_at.isoformat(),
            'last_attempt_at': event.last_attempt_at.isoformat() if event.last_attempt_at else None,
            'last_error': event.last_error
        } for event in events])