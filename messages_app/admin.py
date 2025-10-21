from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin for Message model."""
    
    list_display = ('id', 'sender', 'room', 'org', 'body_preview', 'is_deleted', 'created_at')
    list_filter = ('is_deleted', 'created_at', 'org', 'room')
    search_fields = ('body', 'sender__email', 'sender__first_name', 'sender__last_name', 'room__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('org', 'room', 'sender', 'body', 'file_url')
        }),
        ('Status', {
            'fields': ('is_deleted',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def body_preview(self, obj):
        """Display a preview of the message body."""
        if obj.body:
            return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body
        return 'No text content'
    body_preview.short_description = 'Message Preview'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('sender', 'room', 'org')
