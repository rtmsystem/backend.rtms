"""
WSGI config for RTMS project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import warnings

# Suprimir warnings de pkg_resources deprecado en rest_framework_simplejwt
warnings.filterwarnings(
    'ignore',
    message='pkg_resources is deprecated.*',
    category=UserWarning,
    module='rest_framework_simplejwt'
)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()

