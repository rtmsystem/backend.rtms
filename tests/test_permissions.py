"""
Tests for permission classes.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.authentication.permissions import (
    IsAdmin,
    IsAdminOrOwner,
    IsAdminOrReadOnly,
    IsPlayer,
)
from apps.users.models import UserRole

User = get_user_model()


@pytest.mark.django_db
class TestPermissions:
    """Test permission classes."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = APIRequestFactory()
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role=UserRole.ADMIN
        )
        self.player = User.objects.create_user(
            email='player@test.com',
            password='testpass123',
            role=UserRole.PLAYER
        )

    def test_is_admin_permission(self):
        """Test IsAdmin permission."""
        permission = IsAdmin()
        
        # Test with admin user
        request = self.factory.get('/')
        request.user = self.admin
        assert permission.has_permission(request, None) is True
        
        # Test with player user
        request.user = self.player
        assert permission.has_permission(request, None) is False

    def test_is_player_permission(self):
        """Test IsPlayer permission."""
        permission = IsPlayer()
        
        # Test with player user
        request = self.factory.get('/')
        request.user = self.player
        assert permission.has_permission(request, None) is True
        
        # Test with admin user
        request.user = self.admin
        assert permission.has_permission(request, None) is False

    def test_is_admin_or_owner_permission(self):
        """Test IsAdminOrOwner permission."""
        permission = IsAdminOrOwner()
        
        # Test with admin user
        request = self.factory.get('/')
        request.user = self.admin
        assert permission.has_permission(request, None) is True
        assert permission.has_object_permission(request, None, self.player) is True
        
        # Test with player as owner
        request.user = self.player
        assert permission.has_permission(request, None) is True
        assert permission.has_object_permission(request, None, self.player) is True
        
        # Test with player not as owner
        assert permission.has_object_permission(request, None, self.admin) is False

    def test_is_admin_or_read_only_permission(self):
        """Test IsAdminOrReadOnly permission."""
        permission = IsAdminOrReadOnly()
        
        # Test GET request with player
        request = self.factory.get('/')
        request.user = self.player
        assert permission.has_permission(request, None) is True
        
        # Test POST request with player
        request = self.factory.post('/')
        request.user = self.player
        assert permission.has_permission(request, None) is False
        
        # Test POST request with admin
        request.user = self.admin
        assert permission.has_permission(request, None) is True

