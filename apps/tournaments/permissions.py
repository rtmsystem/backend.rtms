"""
Custom permissions for tournaments app.
"""
from rest_framework import permissions
from .models import TournamentStatus


class IsTournamentOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of a tournament or admins to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the tournament or admins
        return (
            request.user.is_admin or
            obj.organization.administrators.filter(id=request.user.id).exists()
        )


class IsDivisionOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of a tournament division or admins to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the tournament or admins
        return (
            request.user.is_admin or
            obj.tournament.organization.administrators.filter(id=request.user.id).exists()
        )


class CanCreateTournament(permissions.BasePermission):
    """
    Custom permission to only allow users who can create tournaments.
    """
    
    def has_permission(self, request, view):
        # Only authenticated users can create tournaments
        if not request.user.is_authenticated:
            return False
        
        # Admins can always create tournaments
        if request.user.is_admin:
            return True
        
        # Regular users can create tournaments if they are administrators of at least one organization
        return request.user.administered_organizations.exists()


class CanManageTournament(permissions.BasePermission):
    """
    Custom permission to manage tournament (publish, cancel, etc.).
    """
    
    def has_object_permission(self, request, view, obj):
        # Only admins or organization administrators can manage tournaments
        return (
            request.user.is_admin or
            obj.organization.administrators.filter(id=request.user.id).exists()
        )


class CanViewPublishedTournament(permissions.BasePermission):
    """
    Permiso personalizado que permite acceso público a torneos publicados.
    - Usuarios no autenticados pueden ver torneos publicados (solo GET)
    - Usuarios autenticados con permisos pueden ver todos los torneos
    - Solo usuarios con permisos pueden modificar/eliminar
    """
    
    def has_permission(self, request, view):
        # Para métodos GET, permitir acceso público
        if request.method in permissions.SAFE_METHODS:
            return True
        # Para métodos de escritura, requerir autenticación
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Si es un método seguro (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            # Si el torneo está publicado, permitir acceso público
            if obj.status == TournamentStatus.PUBLISHED:
                return True
            # Si no está publicado, solo usuarios autenticados con permisos
            if not request.user or not request.user.is_authenticated:
                return False
            # Usuarios autenticados: admin o administrador de la organización
            return (
                request.user.is_admin or
                obj.organization.administrators.filter(id=request.user.id).exists()
            )
        
        # Para métodos de escritura (PUT, PATCH, DELETE), requerir autenticación y permisos
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            request.user.is_admin or
            obj.organization.administrators.filter(id=request.user.id).exists()
        )
