from rest_framework import serializers
from rooms.models import Room, RoomMember

class RoomSerializer(serializers.ModelSerializer):
    members_count = serializers.IntegerField(source="memberships.count", read_only=True)

    class Meta:
        model = Room
        fields = ["id", "name", "is_dm", "org", "created_by", "created_at", "members_count"]
        read_only_fields = ["created_by", "created_at", "members_count"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["created_by"] = request.user
        room = super().create(validated_data)
        RoomMember.objects.create(room=room, user=request.user)
        return room


class RoomMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomMember
        fields = ["id", "room", "user", "last_read_msg_id", "joined_at"]
        read_only_fields = ["joined_at"]
