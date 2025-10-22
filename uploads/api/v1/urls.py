from django.urls import path
from uploads.views import PresignedUploadView, UserUploadsView

app_name = "uploads_v1"
urlpatterns = [
    path("presign/", PresignedUploadView.as_view(), name="presigned-upload"),
    path("my-uploads/", UserUploadsView.as_view(), name="user-uploads"),
]
