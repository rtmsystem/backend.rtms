"""
Custom permission classes for role-based access control.
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission class to check if user is an Admin.
    """
    message = 'Solo los administradores tienen permiso para realizar esta acción.'
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is an admin."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsPlayer(permissions.BasePermission):
    """
    Permission class to check if user is a Player.
    """
    message = 'Solo los jugadores tienen permiso para realizar esta acción.'
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a player."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_player
        )


class IsAdminOrOwner(permissions.BasePermission):
    """
    Permission class to check if user is an Admin or the owner of the object.
    """
    message = 'No tienes permiso para acceder a este recurso.'
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is admin or owner of the object."""
        # Admins can access everything
        if request.user.is_admin:
            return True
        
        # Check if object belongs to user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object is the user itself
        if obj == request.user:
            return True
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class to allow read-only access to all authenticated users,
    but only admins can modify.
    """
    message = 'Solo los administradores pueden modificar este recurso.'
    
    def has_permission(self, request, view):
        """Check permissions for list/create actions."""
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_admin
    
    def has_object_permission(self, request, view, obj):
        """Check permissions for retrieve/update/delete actions."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_admin

