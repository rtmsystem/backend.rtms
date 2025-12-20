"""
Custom authentication backends for JWT tokens.
"""
import logging
from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication backend for Django REST Framework.
    
    Extends the default JWT authentication to handle custom user model
    and provide better error messages in Spanish.
    """
    
    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[self.get_user_id_claim()]
        except KeyError:
            raise InvalidToken('Token does not contain user information')
        
        try:
            user = User.objects.get(**{self.get_user_id_field(): user_id})
        except User.DoesNotExist:
            raise InvalidToken('User not found')
        
        if not user.is_active:
            raise InvalidToken('User is inactive')
        
        return user
    
    def get_user_id_claim(self):
        """
        Returns the claim key that contains the user identifier.
        """
        return 'user_id'
    
    def get_user_id_field(self):
        """
        Returns the field name that contains the user identifier.
        """
        return 'id'
    
    def authenticate_header(self, request) -> str:
        """
        Return the WWW-Authenticate header value for 401 responses.
        """
        return 'Bearer realm="api"'