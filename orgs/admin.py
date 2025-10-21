from django.contrib import admin
from django.utils import timezone
from .models import Organization, OrganizationMember, OrganizationInvite

class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("joined_at",)
    fields = ("user", "role", "joined_at")

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "member_count")
    search_fields = ("name",)
    ordering = ("-id",)
    inlines = [OrganizationMemberInline]
    readonly_fields = ("created_at",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("members")

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = "Members"

@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "org", "user", "role", "joined_at")
    list_filter = ("role", "joined_at")
    search_fields = ("org__name", "user__email")
    ordering = ("-id",)
    autocomplete_fields = ("org", "user")
    readonly_fields = ("joined_at",)
    list_select_related = ("org", "user")

@admin.register(OrganizationInvite)
class OrganizationInviteAdmin(admin.ModelAdmin):
    list_display = ("id", "org", "email", "role", "created_by", "created_at", "accepted_at", "token_short")
    list_filter = ("role", "created_at", "accepted_at")
    search_fields = ("email", "org__name", "created_by__email", "token")
    ordering = ("-id",)
    autocomplete_fields = ("org", "created_by")
    readonly_fields = ("created_at", "accepted_at", "token")
    fieldsets = (
        (None, {"fields": ("org", "email", "role")}),
        ("Issuer", {"fields": ("created_by",)}),
        ("Token & Timestamps", {"fields": ("token", "created_at", "accepted_at")}),
    )
    actions = ["regenerate_tokens", "mark_accepted_now"]

    @admin.display(description="Token")
    def token_short(self, obj):
        return (obj.token[:12] + "…") if obj.token else ""

    @admin.action(description="Regenerate token for selected invites")
    def regenerate_tokens(self, request, queryset):
        updated = 0
        for inv in queryset:
            inv.token = OrganizationInvite.new_token()
            inv.save(update_fields=["token"])
            updated += 1
        self.message_user(request, f"Regenerated {updated} token(s).")

    @admin.action(description="Mark accepted_at = now()")
    def mark_accepted_now(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(accepted_at=now)
        self.message_user(request, f"Updated {updated} invite(s).")
