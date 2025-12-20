"""
API views for organizations.
"""
from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Organization
from .permissions import (
    CanCreateOrganization,
    CanManageOrganizationAdministrators,
    IsOrganizationAdministrator,
)
from .serializers import (
    AddAdministratorSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
    OrganizationUpdateSerializer,
)
from apps.api.mixins import StandardModelViewSet

User = get_user_model()


class OrganizationViewSet(StandardModelViewSet):
    """
    ViewSet para gestionar organizaciones.
    
    - create: Cualquier usuario autenticado puede crear una organización
              El usuario creador se vuelve administrador automáticamente
    - list: Usuario ve solo organizaciones donde es administrador
    - retrieve: Solo si es administrador de la organización
    - update: Solo administradores de la organización
    - destroy: Solo administradores de la organización
    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    
    def get_permissions(self):
        """
        Retorna los permisos según la acción.
        """
        if self.action == 'create':
            permission_classes = [CanCreateOrganization]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsOrganizationAdministrator]
        elif self.action in ['add_administrator', 'remove_administrator']:
            permission_classes = [CanManageOrganizationAdministrators]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'create':
            return OrganizationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrganizationUpdateSerializer
        return OrganizationSerializer
    
    def get_queryset(self):
        """
        Retorna solo las organizaciones donde el usuario es administrador.
        """
        # Verificar si es una vista fake de Swagger o usuario no autenticado
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Organization.objects.none()  # Retornar queryset vacío para schema generation
        
        user = self.request.user
        return Organization.objects.filter(administrators=user)
    
    @swagger_auto_schema(
        operation_description="Crea una nueva organización. El usuario actual se convierte automáticamente en administrador.",
        request_body=OrganizationCreateSerializer,
        responses={
            201: OrganizationSerializer(),
            400: "Datos inválidos",
            401: "No autenticado"
        },
        security=[{'Bearer': []}]
    )
    def create(self, request, *args, **kwargs):
        """
        Crea una organización.
        El usuario actual se convierte automáticamente en administrador.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            organization = serializer.save()
            output_serializer = OrganizationSerializer(organization)
            return self.created_response(
                data=output_serializer.data,
                message="Organization created successfully"
            )
        else:
            return self.validation_error_response(
                errors=serializer.errors,
                message="Validation error in organization data"
            )
    
    @swagger_auto_schema(
        operation_description="Lista las organizaciones donde el usuario es administrador",
        responses={200: OrganizationSerializer(many=True)},
        security=[{'Bearer': []}]
    )
    def list(self, request, *args, **kwargs):
        """Lista las organizaciones del usuario."""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Obtiene detalles de una organización",
        responses={
            200: OrganizationSerializer(),
            403: "No es administrador de esta organización",
            404: "Organización no encontrada"
        },
        security=[{'Bearer': []}]
    )
    def retrieve(self, request, *args, **kwargs):
        """Obtiene detalles de una organización."""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Actualiza una organización (solo administradores)",
        request_body=OrganizationUpdateSerializer,
        responses={
            200: OrganizationSerializer(),
            400: "Datos inválidos",
            403: "No es administrador",
            404: "Organización no encontrada"
        },
        security=[{'Bearer': []}]
    )
    def update(self, request, *args, **kwargs):
        """Actualiza una organización."""
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Actualiza parcialmente una organización",
        request_body=OrganizationUpdateSerializer,
        responses={
            200: OrganizationSerializer(),
            400: "Datos inválidos",
            403: "No es administrador",
            404: "Organización no encontrada"
        },
        security=[{'Bearer': []}]
    )
    def partial_update(self, request, *args, **kwargs):
        """Actualiza parcialmente una organización."""
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Elimina una organización (solo administradores)",
        responses={
            204: "Organización eliminada",
            403: "No es administrador",
            404: "Organización no encontrada"
        },
        security=[{'Bearer': []}]
    )
    def destroy(self, request, *args, **kwargs):
        """Elimina una organización."""
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    @swagger_auto_schema(
        operation_description="Agrega un administrador a la organización",
        request_body=AddAdministratorSerializer,
        responses={
            200: OrganizationSerializer(),
            400: "Datos inválidos",
            403: "No es administrador",
            404: "Usuario u organización no encontrados"
        },
        security=[{'Bearer': []}]
    )
    def add_administrator(self, request, pk=None):
        """
        Agrega un usuario como administrador de la organización.
        El rol del usuario se cambiará automáticamente a Admin.
        """
        organization = self.get_object()
        serializer = AddAdministratorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(organization)
            output_serializer = OrganizationSerializer(organization)
            return self.success_response(
                data=output_serializer.data,
                message="Administrator added successfully"
            )
        else:
            return self.validation_error_response(
                errors=serializer.errors,
                message="Validation error in administrator data"
            )
    
    @action(detail=True, methods=['post'])
    @swagger_auto_schema(
        operation_description="Remueve un administrador de la organización",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=['user_id']
        ),
        responses={
            200: OrganizationSerializer(),
            400: "Datos inválidos",
            403: "No es administrador",
            404: "Usuario u organización no encontrados"
        },
        security=[{'Bearer': []}]
    )
    def remove_administrator(self, request, pk=None):
        """
        Remueve un administrador de la organización.
        No se puede remover si es el único administrador.
        """
        organization = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return self.error_response(
                message="user_id is required",
                error_code="MISSING_USER_ID",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que no sea el único administrador
        if organization.administrator_count <= 1:
            return self.error_response(
                message="Cannot remove the only administrator of the organization",
                error_code="CANNOT_REMOVE_LAST_ADMIN",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            organization.remove_administrator(user)
            output_serializer = OrganizationSerializer(organization)
            return self.success_response(
                data=output_serializer.data,
                message="Administrator removed successfully"
            )
        except User.DoesNotExist:
            return self.not_found_response(
                message="User not found",
                error_code="USER_NOT_FOUND"
            )

