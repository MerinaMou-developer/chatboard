from rest_framework.permissions import BasePermission, IsAuthenticated
from orgs.models import OrganizationMember

def get_user_role(user, org_id):
    if not user or not user.is_authenticated or not org_id:
        return None
    try:
        return OrganizationMember.objects.only("role").get(org_id=org_id, user=user).role
    except OrganizationMember.DoesNotExist:
        return None

class IsOrgMember(BasePermission):
    def has_permission(self, request, view):
        org_id = getattr(view, "org_id_from_request", lambda r: None)(request)
        role = get_user_role(request.user, org_id)
        return role is not None or bool(getattr(request.user, "is_superuser", False))

class IsOrgManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        org_id = getattr(view, "org_id_from_request", lambda r: None)(request)
        role = get_user_role(request.user, org_id)
        return (role in {"MANAGER", "ADMIN"}) or bool(getattr(request.user, "is_superuser", False))

class IsOrgAdmin(BasePermission):
    def has_permission(self, request, view):
        org_id = getattr(view, "org_id_from_request", lambda r: None)(request)
        role = get_user_role(request.user, org_id)
        return (role == "ADMIN") or bool(getattr(request.user, "is_superuser", False))
