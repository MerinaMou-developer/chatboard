import boto3
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import FileUpload
from .serializers import FileUploadSerializer, PresignedUploadSerializer


class PresignedUploadView(generics.GenericAPIView):
    """Generate presigned URLs for file uploads."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PresignedUploadSerializer
    
    def post(self, request):
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


class UserUploadsView(generics.ListAPIView):
    """List user's uploaded files."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FileUploadSerializer
    
    def get_queryset(self):
        return FileUpload.objects.filter(user=self.request.user)

