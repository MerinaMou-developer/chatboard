from rest_framework import serializers
from uploads.models import FileUpload


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = ['id', 'filename', 'file_size', 'content_type', 'file_url', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class PresignedUploadSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    file_size = serializers.IntegerField(min_value=1, max_value=100 * 1024 * 1024)  # 100MB max
    
    def validate_content_type(self, value):
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'application/zip',
            'video/mp4', 'audio/mpeg', 'audio/wav'
        ]
        if value not in allowed_types:
            raise serializers.ValidationError(f"File type {value} not allowed")
        return value

