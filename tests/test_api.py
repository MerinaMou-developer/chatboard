import pytest
import json
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from orgs.models import Organization, OrganizationMember
from rooms.models import Room, RoomMember
from messages_app.models import Message
from uploads.models import FileUpload

User = get_user_model()


class AuthenticationTestCase(APITestCase):
    """Test authentication endpoints."""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
    
    def test_user_registration(self):
        """Test user registration."""
        url = reverse('auth-register')
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())
    
    def test_user_login(self):
        """Test user login."""
        # Create user first
        user = User.objects.create_user(**self.user_data)
        
        url = reverse('token_obtain_pair')
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_token_refresh(self):
        """Test token refresh."""
        user = User.objects.create_user(**self.user_data)
        refresh = RefreshToken.for_user(user)
        
        url = reverse('token_refresh')
        response = self.client.post(url, {'refresh': str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class OrganizationTestCase(APITestCase):
    """Test organization endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@example.com',
            password='testpass123'
        )
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
    
    def test_create_organization(self):
        """Test organization creation."""
        url = reverse('orgs-list')
        data = {'name': 'Test Organization'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that user becomes admin
        org = Organization.objects.get(name='Test Organization')
        membership = OrganizationMember.objects.get(org=org, user=self.user)
        self.assertEqual(membership.role, OrganizationMember.ADMIN)
    
    def test_list_organizations(self):
        """Test listing user's organizations."""
        # Create organization
        org = Organization.objects.create(name='Test Org')
        OrganizationMember.objects.create(org=org, user=self.user, role=OrganizationMember.ADMIN)
        
        url = reverse('orgs-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Org')


class RoomTestCase(APITestCase):
    """Test room endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(name='Test Organization')
        OrganizationMember.objects.create(
            org=self.org, 
            user=self.user, 
            role=OrganizationMember.ADMIN
        )
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
    
    def test_create_room(self):
        """Test room creation."""
        url = reverse('rooms-list')
        data = {'name': 'Test Room', 'org': self.org.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that user becomes room member
        room = Room.objects.get(name='Test Room')
        membership = RoomMember.objects.get(room=room, user=self.user)
        self.assertIsNotNone(membership)
    
    def test_list_rooms(self):
        """Test listing user's rooms."""
        room = Room.objects.create(name='Test Room', org=self.org, created_by=self.user)
        RoomMember.objects.create(room=room, user=self.user)
        
        url = reverse('rooms-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class MessageTestCase(APITestCase):
    """Test message endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(name='Test Organization')
        self.room = Room.objects.create(name='Test Room', org=self.org, created_by=self.user)
        RoomMember.objects.create(room=self.room, user=self.user)
        
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
    
    def test_send_message(self):
        """Test sending a message."""
        url = reverse('room-messages', kwargs={'room_id': self.room.id})
        data = {'body': 'Hello, world!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check message was created
        message = Message.objects.get(room=self.room, sender=self.user)
        self.assertEqual(message.body, 'Hello, world!')
    
    def test_list_messages(self):
        """Test listing room messages."""
        # Create some messages
        Message.objects.create(
            room=self.room, 
            sender=self.user, 
            body='Message 1',
            org=self.org
        )
        Message.objects.create(
            room=self.room, 
            sender=self.user, 
            body='Message 2',
            org=self.org
        )
        
        url = reverse('room-messages', kwargs={'room_id': self.room.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


class UnreadCountsTestCase(APITestCase):
    """Test unread counts functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.org = Organization.objects.create(name='Test Organization')
        self.room = Room.objects.create(name='Test Room', org=self.org, created_by=self.user)
        self.membership = RoomMember.objects.create(room=self.room, user=self.user)
        
        self.token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
    
    def test_unread_counts(self):
        """Test unread counts endpoint."""
        # Create messages
        Message.objects.create(
            room=self.room, 
            sender=self.user, 
            body='Message 1',
            org=self.org
        )
        
        url = reverse('auth-unread-counts')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['unread_counts']), 1)
        self.assertEqual(response.data['unread_counts'][0]['unread_count'], 0)  # Own message
    
    def test_mark_read(self):
        """Test marking messages as read."""
        # Create a message
        message = Message.objects.create(
            room=self.room, 
            sender=self.user, 
            body='Message 1',
            org=self.org
        )
        
        url = reverse('rooms-mark-read', kwargs={'pk': self.room.id, 'msg_id': message.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check last_read_msg_id was updated
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.last_read_msg_id, message.id)


@override_settings(USE_AWS_S3=False)
class UploadTestCase(APITestCase):
    """Test file upload endpoint when using local storage."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="uploader@example.com",
            password="testpass123",
        )
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_local_file_upload(self):
        url = reverse("uploads_v1:uploads")
        file_obj = SimpleUploadedFile("hello.txt", b"hello world", content_type="text/plain")

        response = self.client.post(url, {"file": file_obj}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("file_url", response.data)
        self.assertTrue(response.data["file_url"].startswith("http"))
        self.assertEqual(FileUpload.objects.count(), 1)
