"""
Custom permission classes for organizations.
"""
from rest_framework import permissions


class IsOrganizationAdministrator(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es administrador de la organización.
    Se usa en acciones de detalle (retrieve, update, delete, etc.)
    """
    message = 'Solo los administradores de esta organización pueden realizar esta acción.'
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica si el usuario es administrador de la organización.
        obj es una instancia de Organization.
        """
        return obj.is_administrator(request.user)


class CanCreateOrganization(permissions.BasePermission):
    """
    Permiso para crear organizaciones.
    Cualquier usuario autenticado puede crear una organización.
    """
    message = 'Debes estar autenticado para crear una organización.'
    
    def has_permission(self, request, view):
        """
        Verifica que el usuario esté autenticado.
        """
        return request.user and request.user.is_authenticated


class CanManageOrganizationAdministrators(permissions.BasePermission):
    """
    Permiso para agregar o remover administradores.
    Solo administradores actuales de la organización.
    """
    message = 'Solo los administradores pueden gestionar otros administradores.'
    
    def has_permission(self, request, view):
        """
        Verifica que el usuario esté autenticado.
        """
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica que el usuario sea administrador de la organización.
        """
        return obj.is_administrator(request.user)

