from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from uploads.models import FileUpload
from uploads.api.base.serializers import FileUploadSerializer
import os

class UploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')

        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Save file to local MEDIA folder (create directories as needed)
        upload_path = os.path.join("uploads", file_obj.name)
        file_path = default_storage.save(upload_path, file_obj)
        storage_url = default_storage.url(file_path)
        file_url = request.build_absolute_uri(storage_url)

        upload = FileUpload.objects.create(
            user=request.user,
            filename=file_obj.name,
            file_size=file_obj.size,
            content_type=file_obj.content_type,
            file_url=file_url
        )

        serializer = FileUploadSerializer(upload)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
