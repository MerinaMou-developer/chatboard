from django.contrib import admin
from .models import Webhook, WebhookOutbox


class WebhookOutboxInline(admin.TabularInline):
    """Inline admin for webhook outbox events."""
    model = WebhookOutbox
    extra = 0
    readonly_fields = ('created_at', 'last_attempt_at')
    fields = ('event_type', 'status', 'retries', 'max_retries', 'next_attempt_at', 'last_error', 'created_at')


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    """Admin for Webhook model."""
    
    list_display = ('id', 'org', 'url_display', 'is_active', 'event_count', 'last_triggered', 'created_at')
    list_filter = ('is_active', 'created_at', 'last_triggered', 'org')
    search_fields = ('url', 'org__name')
    ordering = ('-created_at',)
    readonly_fields = ('secret', 'created_at', 'last_triggered')
    
    inlines = [WebhookOutboxInline]
    
    fieldsets = (
        (None, {
            'fields': ('org', 'url', 'events', 'is_active')
        }),
        ('Security', {
            'fields': ('secret',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_triggered'),
            'classes': ('collapse',)
        }),
    )
    
    def url_display(self, obj):
        """Display a shortened version of the URL."""
        if len(obj.url) > 50:
            return obj.url[:47] + '...'
        return obj.url
    url_display.short_description = 'Webhook URL'
    
    def event_count(self, obj):
        """Display number of events."""
        return len(obj.events) if obj.events else 0
    event_count.short_description = 'Events'


@admin.register(WebhookOutbox)
class WebhookOutboxAdmin(admin.ModelAdmin):
    """Admin for WebhookOutbox model."""
    
    list_display = ('id', 'webhook', 'event_type', 'status', 'retries', 'max_retries', 'next_attempt_at', 'created_at')
    list_filter = ('status', 'retries', 'created_at', 'webhook__org')
    search_fields = ('event_type', 'webhook__url', 'webhook__org__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_attempt_at')
    
    fieldsets = (
        (None, {
            'fields': ('webhook', 'event_type', 'payload')
        }),
        ('Delivery Status', {
            'fields': ('status', 'retries', 'max_retries', 'next_attempt_at', 'last_error')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_attempt_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('webhook', 'webhook__org')
