# System Architecture

This document describes the architecture and design of the RTMS Backend system.

## 📐 Overview

RTMS Backend is a REST API built with Django and Django REST Framework, designed to be consumed by third-party applications. It uses Firebase Authentication for security and PostgreSQL as a database.

```
┌─────────────────────────────────────────────────────────────┐
│                      Client (Frontend)                      │
│           (Web, Mobile, Desktop, Third-party)                │
13: └────────────────────┬────────────────────────────────────────┘
                     │ HTTPS + JWT Token
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (Proxy)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django Application                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   API Layer  │  │  Auth Layer  │  │  Users Layer │     │
│  │              │  │              │  │              │     │
│  │  • REST API  │  │  • Firebase  │  │  • Models    │     │
│  │  • Views     │  │  • JWT       │  │  • Admin     │     │
│  │  • URLs      │  │  • Perms     │  │  • Serializ. │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Django REST Framework                     │    │
│  │  • Serialization  • Permissions  • Pagination      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│   PostgreSQL     │  │  Firebase Admin  │
│   (Database)     │  │  (Auth Service)  │
└──────────────────┘  └──────────────────┘
```

## 🏗️ Application Layers

### 1. Presentation Layer (API Layer)

**Responsibilities:**
- Expose REST endpoints
- Request/response handling
- Input validation
- Documentation (Swagger/OpenAPI)

**Components:**
- `apps/api/views/` - API Views
- `apps/api/urls.py` - Endpoint routes
- `config/urls.py` - Main URLs

### 2. Authentication Layer (Auth Layer)

**Responsibilities:**
- Validate Firebase JWT tokens
- Manage role-based permissions
- Create/link users with Firebase

**Components:**
- `apps/authentication/backends.py` - Authentication backend
- `apps/authentication/permissions.py` - Permission classes
- `apps/authentication/firebase_init.py` - Firebase initialization

### 3. Business Layer

**Responsibilities:**
- Business logic
- Data models
- Business validations
- Data serialization

**Components:**
- `apps/users/models.py` - User models
- `apps/users/serializers.py` - Serializers
- `apps/users/admin.py` - Django Admin

### 4. Data Layer

**Responsibilities:**
- Data persistence
- Optimized queries
- Transactions
- Migrations

**Components:**
- Django ORM
- PostgreSQL
- Django Migrations

## 🔐 Authentication Flow

```
┌─────────┐                                    ┌──────────────┐
│ Client  │                                    │   Firebase   │
└────┬────┘                                    └──────┬───────┘
     │                                                │
     │ 1. Login with credentials                      │
     │──────────────────────────────────────────────>│
     │                                                │
     │ 2. JWT Token                                   │
     │<──────────────────────────────────────────────│
     │                                                │
     │           ┌──────────────────┐                │
     │ 3. GET    │  Django Backend  │                │
     │ /api/v1/* │                  │                │
     │ + Token   │                  │                │
     │──────────>│                  │                │
     │           │                  │ 4. Verify      │
     │           │                  │    Token       │
     │           │                  │───────────────>│
     │           │                  │                │
     │           │                  │ 5. User Info   │
     │           │                  │<───────────────│
     │           │                  │                │
     │           │ 6. Get/Create    │                │
     │           │    User in DB    │                │
     │           │                  │                │
     │ 7. Response                  │                │
     │<──────────│                  │                │
     │           └──────────────────┘                │
```

## 📊 Data Model

### User Model

```python
User
├── id (PK)
├── firebase_uid (unique, indexed)
├── email (unique)
├── first_name
├── last_name
├── role (admin/player)
├── is_active
├── is_staff
├── is_superuser
├── date_joined
└── last_login

Roles:
- ADMIN: Full access
- PLAYER: Limited access
```

### Future Relationships

```
User ──┬── Profile (1:1)
       ├── GameSessions (1:N)
       ├── Achievements (M:N)
       └── Teams (M:N)
```

## 🔑 Permission System

### Permission Hierarchy

```
┌─────────────────────────────────────────┐
│           Superuser (is_superuser)      │
│              Full Access                │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
┌───────▼──────┐  ┌──────▼────────┐
│ Admin Role   │  │  Staff        │
│              │  │  (is_staff)   │
│ • CRUD Users │  │               │
│ • Stats      │  │ • Django      │
│ • All Data   │  │   Admin       │
└──────────────┘  └───────────────┘
        │
        │
┌───────▼──────┐
│ Player Role  │
│              │
│ • Own Data   │
│ • Read Only  │
│ • Limited    │
└──────────────┘
```

### Permission Matrix

| Endpoint | Anonymous | Player | Admin |
|----------|---------|--------|-------|
| GET /api/v1/auth/me/ | ❌ | ✅ (self) | ✅ |
| GET /api/v1/users/ | ❌ | ✅ (self) | ✅ (all) |
| GET /api/v1/users/{id}/ | ❌ | ✅ (self) | ✅ |
| POST /api/v1/users/ | ❌ | ❌ | ✅ |
| PATCH /api/v1/users/{id}/ | ❌ | ✅ (self) | ✅ |
| DELETE /api/v1/users/{id}/ | ❌ | ❌ | ✅ |
| GET /api/v1/users/stats/ | ❌ | ❌ | ✅ |

## 🚀 Request/Response Flow

### Request Pipeline

```
1. Request reaches Nginx
   ↓
2. Nginx forwards to Gunicorn
   ↓
3. Django Middleware Stack
   - SecurityMiddleware
   - SessionMiddleware
   - CorsMiddleware
   - AuthenticationMiddleware
   ↓
4. URL Router
   ↓
5. View/ViewSet
   - Permission Check
   - Validation
   - Business Logic
   ↓
6. Serializer
   - Data Transformation
   - Validation
   ↓
7. Model/Database
   - ORM Queries
   - Database Operations
   ↓
8. Response Serializer
   ↓
9. Response Renderer
   ↓
10. HTTP Response
```

## 📦 Module Structure

### Django Apps

```
apps/
├── api/                 # API endpoints
│   ├── views/           # View logic
│   └── urls.py          # URL routing
│
├── authentication/      # Authentication logic
│   ├── backends.py      # Custom auth backend
│   ├── permissions.py   # Permission classes
│   └── firebase_init.py # Firebase setup
│
└── users/               # User management
    ├── models.py        # User model
    ├── serializers.py   # Data serialization
    └── admin.py         # Admin interface
```

### Configuration

```
config/
├── settings/
│   ├── base.py         # Base settings
│   ├── dev.py          # Development
│   └── prod.py         # Production
│
├── urls.py             # Main URL config
├── wsgi.py             # WSGI entry point
└── asgi.py             # ASGI entry point
```

## 🔄 Design Patterns

### 1. Repository Pattern (via Django ORM)

```python
# models.py
class User(AbstractBaseUser):
    objects = UserManager()  # Custom manager

# Usage
users = User.objects.filter(is_active=True)
```

### 2. Serializer Pattern

```python
# serializers.py
class UserSerializer(serializers.ModelSerializer):
    # Data transformation layer
    pass

# views.py
serializer = UserSerializer(user)
return Response(serializer.data)
```

### 3. Permission Decorator Pattern

```python
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminOrOwner]
```

### 4. Factory Pattern (User Creation)

```python
class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        # Factory method
        pass
```

## 🔧 Environment Configuration

### Development

- DEBUG=True
- SQLite or local PostgreSQL
- Permissive CORS
- Verbose logging
- Email to console

### Production

- DEBUG=False
- Remote PostgreSQL
- Restrictive CORS
- Logging to file
- Mandatory HTTPS
- Gunicorn with multiple workers

## 📈 Scalability

### Horizontal Scaling

```
┌──────────┐
│  Nginx   │ (Load Balancer)
└────┬─────┘
     │
     ├──────────┬──────────┬──────────┐
     │          │          │          │
┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
│Django 1│ │Django 2│ │Django 3│ │Django N│
└────┬───┘ └───┬────┘ └───┬────┘ └───┬────┘
     │         │          │          │
     └─────────┴──────────┴──────────┘
                    │
              ┌─────▼─────┐
              │PostgreSQL │
              │ (Master)  │
              └───────────┘
```

### Caching Strategy (Future)

```
Client → Redis Cache → Django → PostgreSQL
         (Session)     (App)    (Data)
```

## 🔍 Monitoring and Observability

### Logs

```
logs/
├── django.log          # Application logs
├── gunicorn_access.log # Access logs
├── gunicorn_error.log  # Error logs
└── nginx_access.log    # Nginx logs
```

### Key Metrics

- Response time
- Request rate
- Error rate
- Database query time
- Authentication success/failure rate

## 🛡️ Security

### Security Layers

1. **Network**: Firewall, HTTPS
2. **Application**: CSRF, XSS protection
3. **Authentication**: Firebase JWT
4. **Authorization**: Role-based permissions
5. **Data**: PostgreSQL encryption, backups

### Security Headers

```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True  # Production
```

## 🔮 Future Improvements

1. **WebSockets**: Real-time with Django Channels
2. **Caching**: Redis for sessions and cache
3. **Celery**: Asynchronous tasks
4. **ElasticSearch**: Advanced search
5. **GraphQL**: Alternative API
6. **Microservices**: Split into smaller services

---

This document should be updated when the architecture changes significantly.
