"""
Serializers for Organization model.
"""
from django.db import transaction
from rest_framework import serializers

from apps.users.serializers import UserSerializer

from .models import Organization


class OrganizationBasicSerializer(serializers.ModelSerializer):
    """
    Serializer básico para Organization sin relaciones recursivas.
    Usado para incluir en otros serializers.
    """
    # logo_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'nit',
            'is_active',
            'created_at',
            'updated_at',
            'logo',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Organization.
    Usado para mostrar datos (GET).
    """
    administrator_count = serializers.ReadOnlyField()
    administrators = UserSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'nit',
            'administrators',
            'administrator_count',
            'created_by',
            'is_active',
            'created_at',
            'updated_at',
            'logo'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear organizaciones.
    Solo requiere name y nit.
    El usuario que crea la organización se convierte automáticamente en administrador.
    """
    
    class Meta:
        model = Organization
        fields = ['name', 'nit']
    
    def validate_nit(self, value):
        """Valida que el NIT sea único."""
        if Organization.objects.filter(nit=value).exists():
            raise serializers.ValidationError(
                'Ya existe una organización con este NIT.'
            )
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Crea la organización y vincula automáticamente al usuario creador como administrador.
        """
        # Obtener el usuario del contexto (será inyectado desde la vista)
        user = self.context['request'].user
        
        # Crear la organización
        organization = Organization.objects.create(
            name=validated_data['name'],
            nit=validated_data['nit'],
            created_by=user
        )
        
        # Agregar al usuario como administrador
        # Este método también cambiará su rol a Admin automáticamente
        organization.add_administrator(user)
        
        return organization


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar organizaciones.
    Solo permite actualizar name e is_active.
    El NIT no se puede modificar.
    """
    
    class Meta:
        model = Organization
        fields = ['name', 'is_active']


class AddAdministratorSerializer(serializers.Serializer):
    """
    Serializer para agregar un administrador a la organización.
    """
    user_id = serializers.IntegerField()
    
    def validate_user_id(self, value):
        """Valida que el usuario exista."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Usuario no encontrado.')
        
        return value
    
    def save(self, organization):
        """Agrega el usuario como administrador de la organización."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(id=self.validated_data['user_id'])
        organization.add_administrator(user)
        return organization

