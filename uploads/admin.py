from django.contrib import admin
from .models import FileUpload

@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ("id", "filename", "user", "file_size", "content_type", "uploaded_at", "expires_at")
    list_filter = ("content_type", "uploaded_at", "expires_at")
    search_fields = ("filename", "user__email")
    date_hierarchy = "uploaded_at"
    ordering = ("-uploaded_at",)
    autocomplete_fields = ("user",)
    readonly_fields = ("id", "uploaded_at")

    fieldsets = (
        (None, {"fields": ("user", "filename", "file_size", "content_type", "file_url")}),
        ("Timestamps", {"fields": ("uploaded_at", "expires_at")}),
        ("IDs", {"fields": ("id",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user")
