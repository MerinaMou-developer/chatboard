from django.utils.text import slugify
from rest_framework import serializers
from orgs.models import Organization, OrganizationMember, OrganizationInvite
from django.contrib.auth import get_user_model

User = get_user_model()

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "created_at"]

class MemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_first_name = serializers.CharField(source="user.first_name", read_only=True)
    user_last_name = serializers.CharField(source="user.last_name", read_only=True)
    
    class Meta:
        model = OrganizationMember
        fields = ["id", "org", "user", "user_email", "user_first_name", "user_last_name", "role", "joined_at"]
        read_only_fields = ["joined_at"]

class InviteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvite
        fields = ["id", "org", "email", "role"]
        read_only_fields = ["id"]  # Only id is read-only, org comes from URL but needs to be set

    def validate(self, attrs):
        attrs = super().validate(attrs)
        email = attrs.get("email", "").strip().lower()
        org = attrs.get("org")
        # prevent duplicate open invites to same email in same org
        if OrganizationInvite.objects.filter(org=org, email__iexact=email, accepted_at__isnull=True).exists():
            raise serializers.ValidationError("An active invite already exists for this email.")
        attrs["email"] = email
        return attrs

    def create(self, validated):
        request = self.context["request"]
        validated["created_by"] = request.user
        validated["token"] = OrganizationInvite.new_token()
        return super().create(validated)

class InviteAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()
