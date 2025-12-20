#!/bin/bash

# Script de instalación rápida para RTMS Backend
# Uso: ./scripts/setup.sh

set -e

echo "🚀 Iniciando configuración de RTMS Backend..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Verificar Python 3.11
print_info "Verificando Python 3.11..."
if command -v python3.11 &> /dev/null; then
    print_success "Python 3.11 encontrado"
else
    print_error "Python 3.11 no encontrado. Por favor instálalo primero."
    exit 1
fi

# Crear entorno virtual
print_info "Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    print_success "Entorno virtual creado"
else
    print_info "El entorno virtual ya existe"
fi

# Activar entorno virtual
print_info "Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
print_info "Actualizando pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "pip actualizado"

# Instalar dependencias
print_info "Instalando dependencias..."
pip install -r requirements.txt > /dev/null 2>&1
print_success "Dependencias instaladas"

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    print_info "Creando archivo .env..."
    cat > .env << EOF
# Django Settings
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=rtms_db
DB_USER=rtms_user
DB_PASSWORD=rtms_password
DB_HOST=localhost
DB_PORT=5432

# Firebase
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Environment
DJANGO_SETTINGS_MODULE=config.settings.dev
EOF
    print_success "Archivo .env creado"
else
    print_info "El archivo .env ya existe"
fi

# Verificar PostgreSQL
print_info "Verificando conexión a PostgreSQL..."
if command -v psql &> /dev/null; then
    print_success "PostgreSQL encontrado"
    print_info "Por favor, asegúrate de que la base de datos 'rtms_db' exista"
    print_info "Puedes crearla con: createdb rtms_db"
else
    print_error "PostgreSQL no encontrado. Por favor instálalo primero."
    print_info "O usa Docker: docker-compose up -d db"
fi

# Verificar Firebase credentials
if [ ! -f "firebase-credentials.json" ]; then
    print_error "Archivo firebase-credentials.json no encontrado"
    print_info "Por favor, descarga tus credenciales de Firebase y guárdalas como firebase-credentials.json"
    print_info "Ver docs/FIREBASE_SETUP.md para más detalles"
else
    print_success "Credenciales de Firebase encontradas"
fi

# Ejecutar migraciones
print_info "Ejecutando migraciones..."
python manage.py makemigrations > /dev/null 2>&1
python manage.py migrate > /dev/null 2>&1
print_success "Migraciones ejecutadas"

# Crear directorio de logs
mkdir -p logs
print_success "Directorio de logs creado"

# Instalar pre-commit hooks
if command -v pre-commit &> /dev/null; then
    print_info "Instalando pre-commit hooks..."
    pre-commit install > /dev/null 2>&1
    print_success "Pre-commit hooks instalados"
fi

echo ""
print_success "¡Configuración completada!"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Configurar firebase-credentials.json (si no lo has hecho)"
echo "   2. Crear base de datos PostgreSQL si no existe"
echo "   3. Crear superusuario: python manage.py createsuperuser"
echo "   4. O crear usuarios de prueba: python scripts/create_test_users.py"
echo "   5. Ejecutar servidor: python manage.py runserver"
echo ""
echo "📚 Documentación:"
echo "   - README.md"
echo "   - docs/FIREBASE_SETUP.md"
echo "   - docs/API_GUIDE.md"
echo "   - http://localhost:8000/swagger/ (después de iniciar el servidor)"
echo ""

