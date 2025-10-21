# rooms/admin.py
from django.contrib import admin
from .models import Room, RoomMember

class RoomMemberInline(admin.TabularInline):
    model = RoomMember
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("joined_at", "last_read_msg_id")
    fields = ("user", "last_read_msg_id", "joined_at")

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "org", "is_dm", "created_by", "created_at", "member_count")
    list_filter = ("is_dm", "created_at", "org")
    search_fields = ("name", "org__name", "created_by__email")
    ordering = ("-id",)
    date_hierarchy = "created_at"
    autocomplete_fields = ("org", "created_by")
    readonly_fields = ("created_at",)
    inlines = [RoomMemberInline]
    list_select_related = ("org",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("org", "created_by").prefetch_related("memberships")

    def member_count(self, obj):
        return obj.memberships.count()
    member_count.short_description = "Members"

@admin.register(RoomMember)
class RoomMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "user", "last_read_msg_id", "joined_at")
    list_filter = ("joined_at", "room__org")
    search_fields = ("room__name", "user__email", "user__id")
    ordering = ("-id",)
    autocomplete_fields = ("room", "user")
    readonly_fields = ("joined_at",)
    list_select_related = ("room", "user")
    fields = ("room", "user", "last_read_msg_id", "joined_at")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("room", "room__org", "user")
