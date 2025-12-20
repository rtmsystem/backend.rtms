"""
Development settings for RTMS project.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Development specific settings
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Database optimization for development
DATABASES['default']['CONN_MAX_AGE'] = 0

# Disable throttling in development
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/hour',
    'user': '10000/hour'
}

