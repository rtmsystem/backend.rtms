"""
Pytest configuration and fixtures.
"""
import os

import django
import pytest
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()


@pytest.fixture
def api_client():
    """Return DRF API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    from apps.users.models import User, UserRole
    
    user = User.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        role=UserRole.ADMIN,
        first_name='Admin',
        last_name='Test'
    )
    return user


@pytest.fixture
def player_user(db):
    """Create and return a player user."""
    from apps.users.models import User, UserRole
    
    user = User.objects.create_user(
        email='player@test.com',
        password='testpass123',
        role=UserRole.PLAYER,
        first_name='Player',
        last_name='Test'
    )
    return user


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Return API client authenticated as admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def authenticated_player_client(api_client, player_user):
    """Return API client authenticated as player."""
    api_client.force_authenticate(user=player_user)
    return api_client


@pytest.fixture
def authenticated_player_client_with_profile(api_client, player_user):
    """Return API client authenticated as player with profile."""
    from apps.players.models import PlayerProfile
    
    # Create profile if it doesn't exist
    if not hasattr(player_user, 'player_profile'):
        from apps.geographical.models import Country
        country, _ = Country.objects.get_or_create(name='Peru', defaults={'phone_code': '51'})
        
        PlayerProfile.objects.create(
            user=player_user,
            first_name=player_user.first_name,
            last_name=player_user.last_name,
            gender='male',
            nationality=country,
            email=player_user.email,
            date_of_birth='2000-01-01'
        )
    
    api_client.force_authenticate(user=player_user)
    return api_client

