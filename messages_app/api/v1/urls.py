from django.urls import path
from messages_app.api.base.views import RoomMessageListCreateView

app_name = "messages_v1"
urlpatterns = [
    # Room-specific messages
    path("rooms/<int:room_id>/", RoomMessageListCreateView.as_view(), name="room-messages"),
]
