"""
Custom permission classes for player profiles.
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es el propietario del perfil.
    """
    message = 'Solo puedes acceder a tu propio perfil de jugador.'
    
    def has_object_permission(self, request, view, obj):
        """
        Verifica si el usuario es el propietario del perfil.
        obj es una instancia de PlayerProfile.
        Si el perfil no tiene usuario asociado, solo se permite acceso si no hay usuario autenticado.
        """
        if obj.user is None:
            # Si el perfil no tiene usuario, solo permitir si no hay usuario autenticado
            return not request.user or not request.user.is_authenticated
        return obj.user == request.user


class CanCreatePlayerProfile(permissions.BasePermission):
    """
    Permiso para crear perfil de jugador.
    Cualquier usuario autenticado puede crear su perfil.
    """
    message = 'Debes estar autenticado para crear un perfil de jugador.'
    
    def has_permission(self, request, view):
        """
        Verifica que el usuario esté autenticado.
        """
        return request.user and request.user.is_authenticated

