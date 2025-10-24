from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from orgs.models import Organization, OrganizationMember, OrganizationInvite
from .serializers import (
    OrganizationSerializer, MemberSerializer,
    InviteCreateSerializer, InviteAcceptSerializer
)
from config.permissions import IsOrgAdmin, IsOrgManagerOrAdmin, IsOrgMember


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # only orgs where current user is a member
        org_ids = OrganizationMember.objects.filter(user=self.request.user).values_list("org_id", flat=True)
        return Organization.objects.filter(id__in=org_ids)

    def perform_create(self, serializer):
        org = serializer.save()
        OrganizationMember.objects.create(org=org, user=self.request.user, role=OrganizationMember.ADMIN)

    # helper used by permission classes if needed
    def org_id_from_request(self, request):
        return self.kwargs.get("pk") or request.data.get("org")

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated, IsOrgMember]
    )
    def members(self, request, pk=None):
        qs = OrganizationMember.objects.filter(org_id=pk).select_related("user")
        return Response(MemberSerializer(qs, many=True).data)

    @extend_schema(
        request=InviteCreateSerializer,
        responses={201: InviteCreateSerializer},
        description="Invite a user to the organization by email"
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, IsOrgManagerOrAdmin]
    )
    def invite(self, request, pk=None):
        data = request.data.copy()
        data["org"] = pk
        ser = InviteCreateSerializer(data=data, context={"request": request})
        ser.is_valid(raise_exception=True)
        invite = ser.save()
        # Return token for dev; later send email
        return Response(
            {"id": invite.id, "token": invite.token, "email": invite.email, "role": invite.role},
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        request=InviteAcceptSerializer,
        responses={200: {"type": "object", "properties": {"detail": {"type": "string"}, "org_id": {"type": "integer"}, "role": {"type": "string"}}}},
        description="Accept an organization invitation using the invite token"
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="accept-invite"
    )
    def accept_invite(self, request):
        ser = InviteAcceptSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        inv = get_object_or_404(
            OrganizationInvite,
            token=ser.validated_data["token"],
            accepted_at__isnull=True
        )

        # 🔒 Security: ensure the invite email matches the logged-in user
        if request.user.email.lower() != inv.email.lower():
            return Response({"detail": "This invite was sent to a different email."}, status=status.HTTP_403_FORBIDDEN)

        # Upsert membership with invited role
        mem, created = OrganizationMember.objects.get_or_create(
            org=inv.org, user=request.user, defaults={"role": inv.role}
        )
        if not created and mem.role != inv.role:
            # Don't silently downgrade; keep current role
            pass

        inv.accepted_at = timezone.now()
        inv.save(update_fields=["accepted_at"])
        return Response({"detail": "Joined", "org_id": inv.org_id, "role": mem.role}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, IsOrgAdmin],
        url_path="members/(?P<user_id>[^/.]+)/role"
    )
    def change_role(self, request, pk=None, user_id=None):
        new_role = request.data.get("role")
        if new_role not in {"ADMIN", "MANAGER", "MEMBER"}:
            return Response({"detail": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)
        mem = get_object_or_404(OrganizationMember, org_id=pk, user_id=user_id)
        mem.role = new_role
        mem.save(update_fields=["role"])
        return Response({"detail": "Role updated", "user_id": user_id, "role": new_role}, status=status.HTTP_200_OK)
