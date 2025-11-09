from django.urls import path
from uploads.api.base.views import UploadView

app_name = "uploads_v1"
urlpatterns = [
    path("", UploadView.as_view(), name="uploads"),
]
