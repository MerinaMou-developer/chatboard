from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from rooms.models import Room, RoomMember
from .serializers import RoomSerializer, RoomMemberSerializer
from orgs.models import OrganizationMember

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer

    def _user_role_in_org(self, org_id):
        try:
            return OrganizationMember.objects.only("role").get(org_id=org_id, user=self.request.user).role
        except OrganizationMember.DoesNotExist:
            return None

    def get_permissions(self):
        # Create/destroy require MANAGER/ADMIN; others require membership
        if self.action in {"create", "destroy"}:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # Only rooms where the user is a member
        my_room_ids = RoomMember.objects.filter(user=self.request.user).values_list("room_id", flat=True)
        qs = Room.objects.filter(id__in=my_room_ids).select_related("org", "created_by")
        return qs

    def perform_create(self, serializer):
        org = serializer.validated_data.get("org")
        if not org:
            raise ValueError("org is required")
        role = self._user_role_in_org(org.id)
        if role not in {"MANAGER", "ADMIN"}:
            # Only managers/admins can create rooms in an org
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only org MANAGER/ADMIN can create rooms.")
        room = serializer.save(created_by=self.request.user)
        RoomMember.objects.get_or_create(room=room, user=self.request.user)

    @action(detail=True, methods=["post"], url_path="join")
    def join(self, request, pk=None):
        """Join a room."""
        room = self.get_object()
        member, created = RoomMember.objects.get_or_create(
            room=room,
            user=request.user
        )
        if created:
            return Response(
                {"detail": "Successfully joined the room"},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"detail": "Already a member of this room"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="leave")
    def leave(self, request, pk=None):
        """Leave a room."""
        deleted_count, _ = RoomMember.objects.filter(
            room_id=pk,
            user=request.user
        ).delete()
        if deleted_count > 0:
            return Response(
                {"detail": "Successfully left the room"},
                status=status.HTTP_200_OK
            )
        return Response(
            {"detail": "You are not a member of this room"},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, pk=None):
        # Only members can see members
        if not RoomMember.objects.filter(room_id=pk, user=request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Not a member of this room.")
        qs = RoomMember.objects.filter(room_id=pk).select_related("user")
        return Response(RoomMemberSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="read/(?P<msg_id>[^/.]+)")
    def mark_read(self, request, pk=None, msg_id=None):
        """Mark messages as read up to a specific message ID."""
        # Verify user is a member of the room
        membership = get_object_or_404(
            RoomMember, 
            room_id=pk, 
            user=request.user
        )
        
        # Update last_read_msg_id
        membership.last_read_msg_id = int(msg_id)
        membership.save(update_fields=['last_read_msg_id'])
        
        return Response({
            'detail': 'Messages marked as read',
            'room_id': pk,
            'last_read_msg_id': msg_id
        }, status=status.HTTP_200_OK)