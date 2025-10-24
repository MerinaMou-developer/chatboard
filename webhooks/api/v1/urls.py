from django.urls import path
from webhooks.api.base.views import WebhookViewSet

app_name = "webhooks_v1"
urlpatterns = [
    path("", WebhookViewSet.as_view({"get": "list", "post": "create"}), name="webhook-list"),
    path("<int:pk>/", WebhookViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="webhook-detail"),
    path("<int:pk>/test/", WebhookViewSet.as_view({"post": "test_webhook"}), name="webhook-test"),
    path("<int:pk>/events/", WebhookViewSet.as_view({"get": "webhook_events"}), name="webhook-events"),
]

