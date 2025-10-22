from django.urls import path
from rooms.api.base.views import RoomViewSet

app_name = "rooms_v1"
urlpatterns = [
    path("", RoomViewSet.as_view({"get": "list", "post": "create"}), name="room-list"),
    path("<int:pk>/", RoomViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="room-detail"),
    path("<int:pk>/join/", RoomViewSet.as_view({"post": "join"}), name="room-join"),
    path("<int:pk>/leave/", RoomViewSet.as_view({"post": "leave"}), name="room-leave"),
    path("<int:pk>/members/", RoomViewSet.as_view({"get": "members"}), name="room-members"),
]
