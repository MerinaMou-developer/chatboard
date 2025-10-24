from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "org", "room", "sender", "is_deleted", "created_at")
    list_filter = ("is_deleted", "created_at", "org")
    search_fields = ("body", "room__name", "sender__email", "org__name")
    date_hierarchy = "created_at"
    ordering = ("-id",)
    autocomplete_fields = ("org", "room", "sender")
    list_select_related = ("org", "room", "sender")
    readonly_fields = ("created_at",)

    fields = (
        "org",
        "room",
        "sender",
        "body",
        "file_url",
        "is_deleted",
        "created_at",
    )

    actions = ["soft_delete", "restore"]

    @admin.action(description="Soft-delete selected messages")
    def soft_delete(self, request, queryset):
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f"Marked {updated} message(s) as deleted.")

    @admin.action(description="Restore selected messages")
    def restore(self, request, queryset):
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f"Restored {updated} message(s).")
