from django.db import models
from django.conf import settings
import json
import secrets
from datetime import datetime, timedelta


class Webhook(models.Model):
    """Webhook configuration for organizations."""
    org = models.ForeignKey('orgs.Organization', on_delete=models.CASCADE, related_name='webhooks')
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=64, blank=True)
    events = models.JSONField(default=list)  # List of event types to subscribe to
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['org', 'is_active']),
        ]
    
    def __str__(self):
        return f"Webhook {self.id} for {self.org.name}"
    
    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


class WebhookOutbox(models.Model):
    """Outbox pattern for reliable webhook delivery."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]
    
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='outbox_events')
    event_type = models.CharField(max_length=50)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    retries = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    next_attempt_at = models.DateTimeField(default=datetime.now)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'next_attempt_at']),
            models.Index(fields=['webhook', 'status']),
        ]
    
    def __str__(self):
        return f"Outbox {self.id}: {self.event_type} ({self.status})"
    
    def should_retry(self):
        return self.status in ['pending', 'retrying'] and self.retries < self.max_retries
    
    def mark_for_retry(self, error_message=None):
        self.status = 'retrying'
        self.retries += 1
        self.last_error = error_message or ''
        # Exponential backoff: 2^retries minutes
        delay_minutes = 2 ** min(self.retries, 6)  # Cap at 64 minutes
        self.next_attempt_at = datetime.now() + timedelta(minutes=delay_minutes)
        self.last_attempt_at = datetime.now()
        self.save(update_fields=['status', 'retries', 'last_error', 'next_attempt_at', 'last_attempt_at'])
