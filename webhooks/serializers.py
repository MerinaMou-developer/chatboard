from rest_framework import serializers
from .models import Webhook


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ['id', 'url', 'events', 'is_active', 'created_at', 'last_triggered']
        read_only_fields = ['id', 'created_at', 'last_triggered']
    
    def validate_events(self, value):
        allowed_events = [
            'message.created',
            'message.deleted', 
            'member.invited',
            'member.joined',
            'room.created',
            'webhook.test'
        ]
        for event in value:
            if event not in allowed_events:
                raise serializers.ValidationError(f"Event '{event}' is not allowed")
        return value


class WebhookTestSerializer(serializers.Serializer):
    """Serializer for webhook test endpoint."""
    pass

