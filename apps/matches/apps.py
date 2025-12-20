"""
Matches app configuration.
"""
from django.apps import AppConfig


class MatchesConfig(AppConfig):
    """Matches app configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.matches'
    verbose_name = 'Matches'

