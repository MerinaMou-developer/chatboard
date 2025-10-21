from django.conf import settings
from django.db import models
import secrets

class Organization(models.Model):
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-id"]
    def __str__(self): return self.name

class OrganizationMember(models.Model):
    ADMIN, MANAGER, MEMBER = "ADMIN", "MANAGER", "MEMBER"
    ROLE_CHOICES = [(ADMIN,"Admin"), (MANAGER,"Manager"), (MEMBER,"Member")]
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="org_memberships")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default=MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = [("org","user")]
        indexes = [models.Index(fields=["org","user"])]
    def __str__(self): return f"{self.user_id}@{self.org_id}:{self.role}"

class OrganizationInvite(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invites")
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, db_index=True)
    role = models.CharField(max_length=12, choices=OrganizationMember.ROLE_CHOICES, default=OrganizationMember.MEMBER)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_org_invites")
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def new_token():
        return secrets.token_urlsafe(32)
