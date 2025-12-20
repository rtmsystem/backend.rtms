"""
Custom permissions for matches app.
"""
from rest_framework import permissions


class CanViewMatch(permissions.BasePermission):
    """
    Permission to view matches.
    - Public access for viewing matches
    - Authenticated users can view all matches
    """
    
    def has_permission(self, request, view):
        # Allow public access for safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Require authentication for write methods
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Safe methods are allowed for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write methods require authentication
        return request.user and request.user.is_authenticated


class CanManageMatch(permissions.BasePermission):
    """
    Permission to manage matches (create, update, delete).
    Only organization administrators can manage matches.
    """
    
    def has_permission(self, request, view):
        # Require authentication
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins can always manage matches
        if request.user.is_admin:
            return True
        
        # Regular users must be administrators of at least one organization
        return request.user.administered_organizations.exists()
    
    def has_object_permission(self, request, view, obj):
        # Require authentication
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins can always manage matches
        if request.user.is_admin:
            return True
        
        # Check if user is administrator of the tournament's organization
        organization = obj.division.tournament.organization
        return organization.administrators.filter(id=request.user.id).exists()


class CanRecordMatchScore(permissions.BasePermission):
    """
    Permission to record match scores.
    - Organization administrators can always record scores
    - Players involved in the match can record scores
    """
    
    def has_object_permission(self, request, view, obj):
        # Require authentication
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins can always record scores
        if request.user.is_admin:
            return True
        
        # Check if user is administrator of the tournament's organization
        organization = obj.division.tournament.organization
        if organization.administrators.filter(id=request.user.id).exists():
            return True
        
        # Check if user is a player involved in the match
        from apps.players.models import PlayerProfile
        
        try:
            player_profile = request.user.player_profile
        except AttributeError:
            # User doesn't have a player profile
            return False
        
        # Check if player is involved in the match
        is_player = (
            obj.player1_id == player_profile.id or
            obj.player2_id == player_profile.id or
            obj.partner1_id == player_profile.id or
            obj.partner2_id == player_profile.id
        )
        
        return is_player


class CanGenerateBracket(permissions.BasePermission):
    """
    Permission to generate brackets for a division.
    Only organization administrators can generate brackets.
    """
    
    def has_permission(self, request, view):
        # Require authentication
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins can always generate brackets
        if request.user.is_admin:
            return True
        
        # Regular users must be administrators of at least one organization
        return request.user.administered_organizations.exists()

