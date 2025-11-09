from django.db import models
from django.conf import settings
import uuid


class FileUpload(models.Model):
    """Track file uploads for audit and cleanup."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploads")
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=100)
    file_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        related_model = self._meta.get_field("user").related_model
        try:
            user = self.user
        except related_model.DoesNotExist:
            user = None

        if user is not None:
            user_identifier = getattr(user, "email", None) or getattr(user, "username", None) or str(self.user_id)
        else:
            user_identifier = str(self.user_id)

        return f"{self.filename} ({user_identifier})"

