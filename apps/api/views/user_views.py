"""
User management API views.
"""
from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.permissions import IsAdmin, IsAdminOrOwner
from apps.users.serializers import (
    AdminUserUpdateSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from apps.api.mixins import StandardModelViewSet

User = get_user_model()


class UserViewSet(StandardModelViewSet):
    """
    ViewSet for managing users.
    
    - List/Retrieve: Admin can see all, Players can only see themselves
    - Create: Admin only
    - Update: Admin can update any user, Players can only update themselves
    - Delete: Admin only
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdmin]
        elif self.action in ['update', 'partial_update', 'retrieve']:
            permission_classes = [IsAdminOrOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action and user role."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            # Verificar si es una vista fake de Swagger o usuario no autenticado
            if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
                return AdminUserUpdateSerializer  # Default para schema generation
            if self.request.user.is_admin:
                return AdminUserUpdateSerializer
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        """
        Return all users for admins, only current user for players.
        """
        # Verificar si es una vista fake de Swagger o usuario no autenticado
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return User.objects.none()  # Retornar queryset vacío para schema generation
        
        if self.request.user.is_admin:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @swagger_auto_schema(
        operation_description="Lista todos los usuarios (Admin) o el usuario actual (Player)",
        responses={200: UserSerializer(many=True)},
        security=[{'Bearer': []}]
    )
    def list(self, request, *args, **kwargs):
        """List users based on role."""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Obtiene los detalles de un usuario específico",
        responses={
            200: UserSerializer(),
            403: "Sin permisos",
            404: "Usuario no encontrado"
        },
        security=[{'Bearer': []}]
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve user details."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Crea un nuevo usuario (Solo Admin)",
        request_body=UserCreateSerializer,
        responses={
            201: UserSerializer(),
            400: "Datos inválidos",
            403: "Sin permisos"
        },
        security=[{'Bearer': []}]
    )
    def create(self, request, *args, **kwargs):
        """Create new user (Admin only)."""
        return super().create(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Actualiza un usuario (Admin puede actualizar cualquiera, Player solo a sí mismo)",
        request_body=AdminUserUpdateSerializer,
        responses={
            200: UserSerializer(),
            400: "Datos inválidos",
            403: "Sin permisos",
            404: "Usuario no encontrado"
        },
        security=[{'Bearer': []}]
    )
    def update(self, request, *args, **kwargs):
        """Update user."""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Actualiza parcialmente un usuario",
        request_body=AdminUserUpdateSerializer,
        responses={
            200: UserSerializer(),
            400: "Datos inválidos",
            403: "Sin permisos",
            404: "Usuario no encontrado"
        },
        security=[{'Bearer': []}]
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update user."""
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Elimina un usuario (Solo Admin)",
        responses={
            204: "Usuario eliminado",
            403: "Sin permisos",
            404: "Usuario no encontrado"
        },
        security=[{'Bearer': []}]
    )
    def destroy(self, request, *args, **kwargs):
        """Delete user (Admin only)."""
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    @swagger_auto_schema(
        operation_description="Obtiene estadísticas de usuarios (Solo Admin)",
        responses={
            200: openapi.Response(
                description="Estadísticas de usuarios",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_users': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_admins': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_players': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'active_users': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            403: "Sin permisos"
        },
        security=[{'Bearer': []}]
    )
    def stats(self, request):
        """Get user statistics (Admin only)."""
        from apps.users.models import UserRole
        
        total_users = User.objects.count()
        total_admins = User.objects.filter(role=UserRole.ADMIN).count()
        total_players = User.objects.filter(role=UserRole.PLAYER).count()
        active_users = User.objects.filter(is_active=True).count()
        
        return self.success_response(
            data={
                'total_users': total_users,
                'total_admins': total_admins,
                'total_players': total_players,
                'active_users': active_users,
            },
            message="User statistics retrieved successfully"
        )

