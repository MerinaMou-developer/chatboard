from rest_framework import serializers
from rooms.models import Room, RoomMember


class RoomSerializer(serializers.ModelSerializer):
    members_count = serializers.IntegerField(source="memberships.count", read_only=True)

    class Meta:
        model = Room
        fields = ["id", "name", "is_dm", "org", "access_level", "created_by", "created_at", "members_count"]
        read_only_fields = ["created_by", "created_at", "members_count"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["created_by"] = request.user
        room = super().create(validated_data)
        RoomMember.objects.create(room=room, user=request.user)
        return room


class RoomMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_first_name = serializers.CharField(source="user.first_name", read_only=True)
    user_last_name = serializers.CharField(source="user.last_name", read_only=True)
    org_role = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomMember
        fields = ["id", "room", "user", "user_email", "user_first_name", "user_last_name", "org_role", "last_read_msg_id", "joined_at"]
        read_only_fields = ["joined_at"]
    
    def get_org_role(self, obj):
        """Get the user's role in the room's organization."""
        if not obj.room.org:
            return None
        try:
            from orgs.models import OrganizationMember
            org_member = OrganizationMember.objects.get(org=obj.room.org, user=obj.user)
            return org_member.role
        except OrganizationMember.DoesNotExist:
            return None
