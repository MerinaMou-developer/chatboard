from django.urls import path
from uploads.views import PresignedUploadView, DirectUploadView, UserUploadsView

app_name = "uploads_v1"
urlpatterns = [
    # For AWS S3: use presign endpoint to get presigned URL, then upload directly to S3
    # For local: use direct endpoint to upload file to Django server
    path("presign/", PresignedUploadView.as_view(), name="presigned-upload"),  # AWS S3 OR local
    path("direct/", DirectUploadView.as_view(), name="direct-upload"),  # Local only
    path("my-uploads/", UserUploadsView.as_view(), name="user-uploads"),
]
