"""
Tests for API endpoints.
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.users.models import UserRole

User = get_user_model()


@pytest.mark.django_db
class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_current_user_endpoint(self, authenticated_player_client, player_user):
        """Test current user endpoint."""
        url = reverse('api:current-user')
        response = authenticated_player_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == player_user.email
        assert response.data['role'] == UserRole.PLAYER

    def test_current_user_unauthenticated(self, api_client):
        """Test current user endpoint without authentication."""
        url = reverse('api:current-user')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_endpoint(self, authenticated_admin_client, admin_user):
        """Test verify token endpoint."""
        url = reverse('api:verify-token')
        response = authenticated_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True
        assert response.data['user']['email'] == admin_user.email


@pytest.mark.django_db
class TestUserEndpoints:
    """Test user management endpoints."""

    def test_list_users_as_admin(self, authenticated_admin_client):
        """Test listing users as admin."""
        url = reverse('api:user-list')
        response = authenticated_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or isinstance(response.data, list)

    def test_list_users_as_player(self, authenticated_player_client, player_user):
        """Test listing users as player (should only see self)."""
        url = reverse('api:user-list')
        response = authenticated_player_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Player should only see themselves
        results = response.data.get('results', response.data)
        assert len(results) == 1
        assert results[0]['email'] == player_user.email

    def test_create_user_as_admin(self, authenticated_admin_client):
        """Test creating user as admin."""
        url = reverse('api:user-list')
        data = {
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': UserRole.PLAYER
        }
        response = authenticated_admin_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email='newuser@test.com').exists()

    def test_create_user_as_player(self, authenticated_player_client):
        """Test creating user as player (should fail)."""
        url = reverse('api:user-list')
        data = {
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'role': UserRole.PLAYER
        }
        response = authenticated_player_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_self_as_player(self, authenticated_player_client, player_user):
        """Test player updating their own information."""
        url = reverse('api:user-detail', kwargs={'pk': player_user.pk})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = authenticated_player_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        player_user.refresh_from_db()
        assert player_user.first_name == 'Updated'
        assert player_user.last_name == 'Name'

    def test_update_other_user_as_player(self, authenticated_player_client, admin_user):
        """Test player updating another user (should fail)."""
        url = reverse('api:user-detail', kwargs={'pk': admin_user.pk})
        data = {
            'first_name': 'Hacked'
        }
        response = authenticated_player_client.patch(url, data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_user_as_admin(self, authenticated_admin_client, player_user):
        """Test deleting user as admin."""
        url = reverse('api:user-detail', kwargs={'pk': player_user.pk})
        response = authenticated_admin_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(pk=player_user.pk).exists()

    def test_delete_user_as_player(self, authenticated_player_client, admin_user):
        """Test deleting user as player (should fail)."""
        url = reverse('api:user-detail', kwargs={'pk': admin_user.pk})
        response = authenticated_player_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_stats_as_admin(self, authenticated_admin_client):
        """Test user statistics endpoint as admin."""
        url = reverse('api:user-stats')
        response = authenticated_admin_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_users' in response.data
        assert 'total_admins' in response.data
        assert 'total_players' in response.data
        assert 'active_users' in response.data

    def test_user_stats_as_player(self, authenticated_player_client):
        """Test user statistics endpoint as player (should fail)."""
        url = reverse('api:user-stats')
        response = authenticated_player_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

