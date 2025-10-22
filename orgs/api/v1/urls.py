from django.urls import path
from orgs.api.base.views import OrganizationViewSet

app_name = "orgs_v1"
urlpatterns = [
    path("", OrganizationViewSet.as_view({"get": "list", "post": "create"}), name="org-list"),
    path("<int:pk>/", OrganizationViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="org-detail"),
    path("<int:pk>/members/", OrganizationViewSet.as_view({"get": "members"}), name="org-members"),
    path("<int:pk>/invite/", OrganizationViewSet.as_view({"post": "invite"}), name="org-invite"),
    path("accept-invite/", OrganizationViewSet.as_view({"post": "accept_invite"}), name="org-accept-invite"),
    path("<int:pk>/members/<int:user_id>/role/", OrganizationViewSet.as_view({"post": "change_role"}), name="org-change-role"),
]
