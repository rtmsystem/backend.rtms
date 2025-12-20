"""
Tests for User model and authentication.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.users.models import UserRole

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test User model."""

    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.role == UserRole.PLAYER
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password('testpass123')

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        
        assert user.email == 'admin@example.com'
        assert user.role == UserRole.ADMIN
        assert user.is_active is True
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_user_str(self):
        """Test user string representation."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert str(user) == 'test@example.com'

    def test_user_full_name(self):
        """Test user full_name property."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        assert user.full_name == 'John Doe'

    def test_is_admin_property(self):
        """Test is_admin property."""
        admin = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            role=UserRole.ADMIN
        )
        player = User.objects.create_user(
            email='player@example.com',
            password='testpass123',
            role=UserRole.PLAYER
        )
        
        assert admin.is_admin is True
        assert player.is_admin is False

    def test_is_player_property(self):
        """Test is_player property."""
        admin = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            role=UserRole.ADMIN
        )
        player = User.objects.create_user(
            email='player@example.com',
            password='testpass123',
            role=UserRole.PLAYER
        )
        
        assert admin.is_player is False
        assert player.is_player is True

