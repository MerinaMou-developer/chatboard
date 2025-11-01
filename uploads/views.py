import boto3
import uuid
import os
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import FileUpload
from .serializers import FileUploadSerializer, PresignedUploadSerializer


class PresignedUploadView(generics.GenericAPIView):
    """Generate presigned URLs for file uploads (AWS S3) OR accept direct uploads (local storage)."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_parser_classes(self):
        """Return appropriate parser based on storage mode."""
        if settings.USE_AWS_S3:
            # For AWS S3, parse JSON data
            return super().get_parser_classes()
        else:
            # For local storage, parse multipart/form-data
            return [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on storage mode."""
        return PresignedUploadSerializer
    
    def post(self, request):
        """Handle file upload request based on storage configuration."""
        if settings.USE_AWS_S3:
            return self._handle_s3_upload(request)
        else:
            return self._handle_local_upload(request)
    
    def _handle_s3_upload(self, request):
        """AWS S3 presigned URL approach."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        filename = serializer.validated_data['filename']
        content_type = serializer.validated_data['content_type']
        file_size = serializer.validated_data['file_size']
        
        # Generate unique key for S3
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
        s3_key = f"uploads/{request.user.id}/{unique_filename}"
        
        # Configure S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # Generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': s3_key,
                'ContentType': content_type,
                'ContentLength': file_size,
            },
            ExpiresIn=3600  # 1 hour
        )
        
        # Generate file URL for after upload
        file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"
        
        # Store upload record
        upload_record = FileUpload.objects.create(
            user=request.user,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            file_url=file_url,
            expires_at=datetime.now() + timedelta(days=30)  # Files expire after 30 days
        )
        
        return Response({
            'upload_url': presigned_url,
            'file_url': file_url,
            'upload_id': str(upload_record.id),
            'expires_in': 3600
        }, status=status.HTTP_200_OK)
    
    def _handle_local_upload(self, request):
        """Local file storage - accept file directly."""
        # Check if file is in request (direct upload)
        if 'file' in request.FILES:
            file = request.FILES['file']
            filename = request.data.get('filename', file.name)
            content_type = file.content_type
            file_size = file.size
        else:
            # No file provided, return error
            return Response({
                'error': 'No file provided. For local storage, send the file in the request.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'application/zip',
            'video/mp4', 'audio/mpeg', 'audio/wav'
        ]
        if content_type not in allowed_types:
            return Response({
                'error': f'File type {content_type} not allowed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file size (100MB max)
        if file_size > 100 * 1024 * 1024:
            return Response({
                'error': 'File size exceeds 100MB limit'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate unique filename
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
        
        # Create user-specific directory
        user_upload_dir = settings.MEDIA_ROOT / "uploads" / str(request.user.id)
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Save file
        file_path = user_upload_dir / unique_filename
        with open(file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        
        # Generate file URL
        file_url = f"{settings.MEDIA_URL}uploads/{request.user.id}/{unique_filename}"
        # For absolute URL in production, you might want to use request.build_absolute_uri(file_url)
        
        # Store upload record
        upload_record = FileUpload.objects.create(
            user=request.user,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            file_url=file_url,
            expires_at=datetime.now() + timedelta(days=30)
        )
        
        return Response({
            'upload_id': str(upload_record.id),
            'file_url': file_url,
            'message': 'File uploaded successfully'
        }, status=status.HTTP_201_CREATED)


class DirectUploadView(generics.GenericAPIView):
    """Alternative direct upload endpoint (only for local storage, more RESTful)."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Accept file directly via multipart/form-data."""
        if settings.USE_AWS_S3:
            return Response({
                'error': 'Direct upload not available for S3. Use presigned URL endpoint.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return PresignedUploadView()._handle_local_upload(request)


class UserUploadsView(generics.ListAPIView):
    """List user's uploaded files."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileUploadSerializer
    
    def get_queryset(self):
        return FileUpload.objects.filter(user=self.request.user)
