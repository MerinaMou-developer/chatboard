from django.urls import path
from notifications.api.base.views import NotificationViewSet

app_name = "notifications_v1"
urlpatterns = [
    path("", NotificationViewSet.as_view({"get": "list"}), name="notification-list"),
    path("<int:pk>/", NotificationViewSet.as_view({"get": "retrieve", "patch": "partial_update"}), name="notification-detail"),
    path("mark-all-read/", NotificationViewSet.as_view({"post": "mark_all_read"}), name="notification-mark-all-read"),
    path("unread-count/", NotificationViewSet.as_view({"get": "unread_count"}), name="notification-unread-count"),
]