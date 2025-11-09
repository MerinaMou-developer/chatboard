from rest_framework import serializers
from messages_app.models import Message

class MessageSerializer(serializers.ModelSerializer):
    room = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Message
        fields = ["id", "org", "room", "sender", "body", "file_url", "is_deleted", "created_at"]
        read_only_fields = ["org", "room", "sender", "is_deleted", "created_at"]
        extra_kwargs = {"room": {"read_only": True}}

    def validate(self, attrs):
        body = attrs.get("body", "") or ""
        file_url = attrs.get("file_url")
        if not body.strip() and not file_url:
            raise serializers.ValidationError("Either 'body' or 'file_url' is required.")
        return attrs
