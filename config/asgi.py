"""
ASGI config for RTMS project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
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

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_asgi_application()

