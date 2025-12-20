# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2024-01-20

### ✨ Añadido

#### Core
- Proyecto Django 5.0 con Python 3.11
- Django REST Framework para API REST
- Estructura modular de settings (base, dev, prod)
- Configuración de CORS
- Logging configurado
- Soporte para operaciones asíncronas
- Django Channels preparado para WebSockets

#### Autenticación
- Integración con Firebase Authentication
- Backend de autenticación personalizado con JWT
- Middleware de autenticación Firebase
- Verificación de tokens JWT

#### Usuarios
- Modelo de usuario customizado (AbstractBaseUser)
- Sistema de roles: Admin y Player
- Permisos granulares por rol
- Serializers para diferentes operaciones
- Admin de Django personalizado

#### API
- Endpoints RESTful completos para gestión de usuarios
- Versionado de API (v1)
- Paginación automática
- Throttling (rate limiting)
- Filtrado y búsqueda

#### Permisos
- `IsAdmin`: Solo administradores
- `IsPlayer`: Solo jugadores
- `IsAdminOrOwner`: Admin o dueño del recurso
- `IsAdminOrReadOnly`: Lectura para todos, escritura solo admin

#### Documentación
- Swagger UI integrado
- ReDoc integrado
- Colección de Postman
- Guías de configuración
- Ejemplos de integración

#### Tests
- Tests de modelo de usuario
- Tests de permisos
- Tests de endpoints API
- Fixtures de pytest
- Configuración de pytest-django

#### DevOps
- Dockerfile optimizado
- docker-compose.yml con PostgreSQL
- Configuración de Nginx
- Guía de despliegue completa
- Scripts de inicialización

#### Calidad de Código
- Pre-commit hooks configurados
- Black para formateo
- isort para ordenar imports
- flake8 para linting
- mypy para type checking
- Configuración de editorconfig

#### Documentación
- README completo
- Guía de inicio rápido (QUICKSTART.md)
- Guía de configuración de Firebase (FIREBASE_SETUP.md)
- Guía de API (API_GUIDE.md)
- Guía de despliegue (DEPLOYMENT.md)
- Changelog

#### Scripts Utilitarios
- Script de setup automático
- Script de inicialización de DB
- Script para crear usuarios de prueba
- Makefile con comandos útiles

### 🔧 Configuración

- PostgreSQL como base de datos
- Gunicorn como servidor WSGI
- Supervisor para gestión de procesos
- Variables de entorno para configuración

### 📦 Dependencias Principales

- Django 5.0.1
- djangorestframework 3.14.0
- firebase-admin 6.4.0
- psycopg2-binary 2.9.9
- django-cors-headers 4.3.1
- drf-yasg 1.21.7
- channels 4.0.0

### 🔒 Seguridad

- Autenticación mediante Firebase JWT
- CORS configurado correctamente
- Validación de tokens
- Permisos granulares
- Settings seguros para producción

---

## Tipos de Cambios

- **✨ Añadido**: Para nuevas características
- **🔧 Cambiado**: Para cambios en funcionalidad existente
- **🐛 Corregido**: Para corrección de bugs
- **🗑️ Eliminado**: Para características eliminadas
- **🔒 Seguridad**: Para vulnerabilidades de seguridad
- **📚 Documentación**: Para cambios en documentación
- **⚡ Performance**: Para mejoras de rendimiento

