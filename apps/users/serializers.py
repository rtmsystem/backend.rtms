"""
Serializers for User model.
"""
from rest_framework import serializers

from .models import User, UserRole


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    full_name = serializers.ReadOnlyField()
    is_admin = serializers.ReadOnlyField()
    is_player = serializers.ReadOnlyField()
    organization = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'is_admin',
            'is_player',
            'is_active',
            'date_joined',
            'last_login',
            'avatar',
            'organization',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_organization(self, obj):
        """Returns organizations associated with the user."""
        from apps.organizations.serializers import OrganizationBasicSerializer
        organizations = obj.administered_organizations.filter(is_active=True).first()
        return OrganizationBasicSerializer(organizations).data


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users."""
    
    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'role',
            'password',
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        """Create user with encrypted password."""
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users."""
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'is_active',
        ]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updating any user."""
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'role',
            'is_active',
        ]

