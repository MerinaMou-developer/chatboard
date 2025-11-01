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
        
        # Smart auto-join based on access level
        access_level = room.access_level
        org_members = OrganizationMember.objects.filter(org=room.org)
        
        for member in org_members:
            user_role = member.role
            
            # Determine if user should auto-join
            should_join = False
            if access_level == Room.PUBLIC:
                should_join = True  # All org members
            elif access_level == Room.MANAGER_ONLY:
                should_join = user_role in {"MANAGER", "ADMIN"}  # Only managers/admins
            elif access_level == Room.PRIVATE:
                should_join = False  # No auto-join for private rooms
            
            if should_join:
                RoomMember.objects.get_or_create(room=room, user=member.user)

    @action(detail=True, methods=["post"], url_path="join")
    def join(self, request, pk=None):
        """Join a room."""
        room = self.get_object()
        
        # Check if user is member of the room's organization
        if room.org:
            try:
                org_membership = OrganizationMember.objects.get(org=room.org, user=request.user)
                user_role = org_membership.role
            except OrganizationMember.DoesNotExist:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You must be a member of this organization to join the room.")
        else:
            user_role = None
        
        # Check access level restrictions
        if room.access_level == Room.MANAGER_ONLY:
            if user_role not in {"MANAGER", "ADMIN"}:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("This room is restricted to managers and admins only.")
        elif room.access_level == Room.PRIVATE:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This room is private. You need an invitation to join.")
        
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

    @action(detail=True, methods=["post"], url_path="invite")
    def invite_user(self, request, pk=None):
        """Invite a user to a private room."""
        room = self.get_object()
        
        # Only room creator or org admin can invite
        if room.created_by != request.user:
            role = self._user_role_in_org(room.org.id) if room.org else None
            if role != "ADMIN":
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Only room creator or org admin can invite users.")
        
        # Only private rooms need invites
        if room.access_level != Room.PRIVATE:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Only private rooms require invitations.")
        
        user_id = request.data.get("user_id")
        if not user_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("user_id is required.")
        
        # Check if user is org member
        try:
            org_membership = OrganizationMember.objects.get(org=room.org, user_id=user_id)
        except OrganizationMember.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("User must be a member of the organization.")
        
        # Add user to room
        member, created = RoomMember.objects.get_or_create(
            room=room,
            user_id=user_id
        )
        
        if created:
            return Response(
                {"detail": "User successfully invited to the room"},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"detail": "User is already a member of this room"},
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