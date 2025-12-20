"""
Tests for organizations module.
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.organizations.models import Organization
from apps.users.models import UserRole

User = get_user_model()


@pytest.mark.django_db
class TestOrganizationModel:
    """Tests para el modelo Organization."""

    def test_create_organization(self):
        """Test crear una organización."""
        org = Organization.objects.create(
            name='Test Organization',
            nit='123456789'
        )
        
        assert org.name == 'Test Organization'
        assert org.nit == '123456789'
        assert org.is_active is True
        assert org.administrator_count == 0
        assert str(org) == 'Test Organization (123456789)'

    def test_add_administrator_changes_role(self):
        """Test que agregar administrador cambia el rol del usuario a Admin."""
        org = Organization.objects.create(
            name='Test Org',
            nit='123'
        )
        
        user = User.objects.create_user(
            email='user@test.com',
            password='pass123',
            role=UserRole.PLAYER
        )
        
        assert user.role == UserRole.PLAYER
        
        # Agregar como administrador
        org.add_administrator(user)
        
        # Verificar que el rol cambió
        user.refresh_from_db()
        assert user.role == UserRole.ADMIN
        assert org.is_administrator(user)
        assert org.administrator_count == 1

    def test_remove_administrator(self):
        """Test remover un administrador."""
        org = Organization.objects.create(
            name='Test Org',
            nit='123'
        )
        
        user = User.objects.create_user(
            email='admin@test.com',
            password='pass123',
            role=UserRole.ADMIN
        )
        
        org.add_administrator(user)
        assert org.is_administrator(user)
        
        org.remove_administrator(user)
        assert not org.is_administrator(user)
        assert org.administrator_count == 0

    def test_multiple_administrators(self):
        """Test que una organización puede tener múltiples administradores."""
        org = Organization.objects.create(
            name='Test Org',
            nit='123'
        )
        
        user1 = User.objects.create_user(email='user1@test.com', password='pass')
        user2 = User.objects.create_user(email='user2@test.com', password='pass')
        
        org.add_administrator(user1)
        org.add_administrator(user2)
        
        assert org.administrator_count == 2
        assert org.is_administrator(user1)
        assert org.is_administrator(user2)


@pytest.mark.django_db
class TestOrganizationAPI:
    """Tests para los endpoints de la API de organizaciones."""

    def test_create_organization_as_authenticated_user(self, authenticated_player_client, player_user):
        """Test que un usuario autenticado puede crear una organización."""
        url = reverse('api:organization-list')
        data = {
            'name': 'New Organization',
            'nit': '987654321'
        }
        
        # Usuario era player
        assert player_user.role == UserRole.PLAYER
        
        response = authenticated_player_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Organization.objects.filter(nit='987654321').exists()
        
        org = Organization.objects.get(nit='987654321')
        
        # Verificar que el usuario es ahora admin
        player_user.refresh_from_db()
        assert player_user.role == UserRole.ADMIN
        
        # Verificar que el usuario está como administrador
        assert org.is_administrator(player_user)
        assert org.created_by == player_user
        assert org.administrator_count == 1

    def test_create_organization_with_duplicate_nit(self, authenticated_player_client):
        """Test que no se puede crear organización con NIT duplicado."""
        Organization.objects.create(name='Existing', nit='123456')
        
        url = reverse('api:organization-list')
        data = {
            'name': 'New Organization',
            'nit': '123456'  # NIT duplicado
        }
        
        response = authenticated_player_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'nit' in response.data['errors']

    def test_list_organizations_shows_only_user_orgs(self, authenticated_player_client, player_user):
        """Test que listar organizaciones muestra solo las del usuario."""
        # Crear organización del usuario
        org1 = Organization.objects.create(name='My Org', nit='111')
        org1.add_administrator(player_user)
        
        # Crear organización de otro usuario
        other_user = User.objects.create_user(email='other@test.com', password='pass')
        org2 = Organization.objects.create(name='Other Org', nit='222')
        org2.add_administrator(other_user)
        
        url = reverse('api:organization-list')
        response = authenticated_player_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['name'] == 'My Org'

    def test_retrieve_organization_as_administrator(self, authenticated_player_client, player_user):
        """Test que un administrador puede ver detalles de su organización."""
        org = Organization.objects.create(name='Test Org', nit='123')
        org.add_administrator(player_user)
        
        url = reverse('api:organization-detail', kwargs={'pk': org.pk})
        response = authenticated_player_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == 'Test Org'
        assert response.data['data']['nit'] == '123'

    def test_retrieve_organization_non_administrator_fails(self, authenticated_player_client, player_user):
        """Test que un usuario no puede ver organizaciones donde no es admin."""
        other_user = User.objects.create_user(email='other@test.com', password='pass')
        org = Organization.objects.create(name='Other Org', nit='123')
        org.add_administrator(other_user)
        
        url = reverse('api:organization-detail', kwargs={'pk': org.pk})
        response = authenticated_player_client.get(url)
        
        # 404 porque get_queryset() filtra la org
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_organization_as_administrator(self, authenticated_player_client, player_user):
        """Test que un administrador puede actualizar su organización."""
        org = Organization.objects.create(name='Old Name', nit='123')
        org.add_administrator(player_user)
        
        url = reverse('api:organization-detail', kwargs={'pk': org.pk})
        data = {'name': 'New Name'}
        
        response = authenticated_player_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        org.refresh_from_db()
        assert org.name == 'New Name'

    def test_update_organization_non_administrator_fails(self, authenticated_player_client, player_user):
        """Test que un usuario no puede actualizar organizaciones donde no es admin."""
        other_user = User.objects.create_user(email='other@test.com', password='pass')
        org = Organization.objects.create(name='Test Org', nit='123')
        org.add_administrator(other_user)
        
        url = reverse('api:organization-detail', kwargs={'pk': org.pk})
        data = {'name': 'Hacked Name'}
        
        response = authenticated_player_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        org.refresh_from_db()
        assert org.name == 'Test Org'  # No cambió

    def test_delete_organization_as_administrator(self, authenticated_player_client, player_user):
        """Test que un administrador puede eliminar su organización."""
        org = Organization.objects.create(name='Test Org', nit='123')
        org.add_administrator(player_user)
        
        url = reverse('api:organization-detail', kwargs={'pk': org.pk})
        response = authenticated_player_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Organization.objects.filter(pk=org.pk).exists()

    def test_add_administrator_to_organization(self, authenticated_admin_client, admin_user):
        """Test agregar un administrador a la organización."""
        org = Organization.objects.create(name='Test Org', nit='123')
        org.add_administrator(admin_user)
        
        # Crear nuevo usuario para agregar
        new_user = User.objects.create_user(
            email='newadmin@test.com',
            password='pass',
            role=UserRole.PLAYER
        )
        
        assert new_user.role == UserRole.PLAYER
        
        url = reverse('api:organization-add-administrator', kwargs={'pk': org.pk})
        data = {'user_id': new_user.id}
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert org.is_administrator(new_user)
        
        # Verificar que el rol cambió a admin
        new_user.refresh_from_db()
        assert new_user.role == UserRole.ADMIN

    def test_remove_administrator_from_organization(self, authenticated_admin_client, admin_user):
        """Test remover un administrador de la organización."""
        org = Organization.objects.create(name='Test Org', nit='123')
        org.add_administrator(admin_user)
        
        # Agregar segundo admin
        second_admin = User.objects.create_user(email='admin2@test.com', password='pass')
        org.add_administrator(second_admin)
        
        assert org.administrator_count == 2
        
        url = reverse('api:organization-remove-administrator', kwargs={'pk': org.pk})
        data = {'user_id': second_admin.id}
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert not org.is_administrator(second_admin)
        assert org.administrator_count == 1

    def test_cannot_remove_last_administrator(self, authenticated_admin_client, admin_user):
        """Test que no se puede remover al único administrador."""
        org = Organization.objects.create(name='Test Org', nit='123')
        org.add_administrator(admin_user)
        
        url = reverse('api:organization-remove-administrator', kwargs={'pk': org.pk})
        data = {'user_id': admin_user.id}
        
        response = authenticated_admin_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'only administrator' in response.data['message']
        assert org.is_administrator(admin_user)  # Sigue siendo admin

    def test_unauthenticated_user_cannot_create_organization(self, api_client):
        """Test que un usuario no autenticado no puede crear organizaciones."""
        url = reverse('api:organization-list')
        data = {
            'name': 'Test Org',
            'nit': '123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOrganizationPermissions:
    """Tests para verificar los permisos de organizaciones."""

    def test_user_can_only_see_their_organizations(self, authenticated_player_client, player_user):
        """Test que un usuario solo ve sus organizaciones."""
        # Crear org del usuario
        ...

    def test_non_admin_cannot_manage_administrators(self, authenticated_player_client, player_user):
        """Test que un usuario no puede agregar admins a orgs donde no es admin."""
        other_user = User.objects.create_user(email='other@test.com', password='pass')
        org = Organization.objects.create(name='Other Org', nit='123')
        org.add_administrator(other_user)
        
        new_user = User.objects.create_user(email='new@test.com', password='pass')
        
        url = reverse('api:organization-add-administrator', kwargs={'pk': org.pk})
        data = {'user_id': new_user.id}
        
        response = authenticated_player_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

