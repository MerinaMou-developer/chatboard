from django.urls import path
from .views import PresignedUploadView, UserUploadsView

urlpatterns = [
    path('presign/', PresignedUploadView.as_view(), name='presigned-upload'),
    path('my-uploads/', UserUploadsView.as_view(), name='user-uploads'),
]

