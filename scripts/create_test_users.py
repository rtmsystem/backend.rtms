"""
Script para crear usuarios de prueba.
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import UserRole

User = get_user_model()


def create_test_users():
    """Crear usuarios de prueba si no existen."""
    
    # Admin user
    if not User.objects.filter(email='admin@test.com').exists():
        admin = User.objects.create_superuser(
            email='admin@test.com',
            password='admin123',
            first_name='Admin',
            last_name='Test'
        )
        print(f"✅ Admin creado: {admin.email}")
    else:
        print("ℹ️  Admin ya existe")
    
    # Player user
    if not User.objects.filter(email='player@test.com').exists():
        player = User.objects.create_user(
            email='player@test.com',
            password='player123',
            first_name='Player',
            last_name='Test',
            role=UserRole.PLAYER
        )
        print(f"✅ Player creado: {player.email}")
    else:
        print("ℹ️  Player ya existe")
    
    print("\n📝 Credenciales de prueba:")
    print("Admin: admin@test.com / admin123")
    print("Player: player@test.com / player123")


if __name__ == '__main__':
    create_test_users()

