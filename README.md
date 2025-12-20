# Backend RTMS - Real-Time Management System

REST API built with Django and Django REST Framework to be consumed by third parties. Includes Firebase authentication, user roles (Admin/Player), and support for asynchronous operations.

## 🚀 Features

- **Django 5.0** with Python 3.11
- **Django REST Framework** for REST API
- **Firebase Authentication** with JWT tokens
- **PostgreSQL** as database
- **User Roles**: Admin and Player with differentiated permissions
- **Asynchronous Support** for views and operations
- **Docker and Docker Compose** for development and deployment
- **Swagger/OpenAPI** for automatic API documentation
- **Pre-commit hooks** with linters (black, flake8, isort, mypy)
- **Tests** with pytest
- **CORS** configured to allow integrations with frontends

## 📋 Prerequisites

- Python 3.11
- PostgreSQL 15+
- Docker and Docker Compose (optional)
- Firebase account with service credentials

## 🛠️ Local Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd backend.rtms
```

### 2. Create virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env` file in the project root (use `.env.example` as a reference):

```bash
# Django Settings
SECRET_KEY=your-super-secure-secret-key-here
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
```

### 5. Configure Firebase

1. Go to Firebase Console → Project Settings → Service Accounts
2. Generate new private key
3. Download the JSON file
4. Save it as `firebase-credentials.json` in the project root

### 6. Configure PostgreSQL

**Option A: Local PostgreSQL**

```bash
# Create database
psql -U postgres
CREATE DATABASE rtms_db;
CREATE USER rtms_user WITH PASSWORD 'rtms_password';
GRANT ALL PRIVILEGES ON DATABASE rtms_db TO rtms_user;
\q
```

**Option B: Docker (recommended)**

```bash
docker run -d \
  --name rtms_postgres \
  -e POSTGRES_DB=rtms_db \
  -e POSTGRES_USER=rtms_user \
  -e POSTGRES_PASSWORD=rtms_password \
  -p 5432:5432 \
  postgres:15
```

### 7. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Create superuser

```bash
python manage.py createsuperuser
```

Or create test users:

```bash
python scripts/create_test_users.py
```

### 9. Run development server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000`

## 🐳 Installation with Docker

### 1. Configure environment variables

Create `.env` file with the necessary configurations.

### 2. Build and start containers

```bash
docker-compose up --build
```

### 3. Run migrations

```bash
docker-compose exec web python manage.py migrate
```

### 4. Create superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

## 📚 API Documentation

Once the server is running, you can access the interactive documentation at:

- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`
- **Schema JSON**: `http://localhost:8000/swagger.json`

## 🔐 Authentication

The API uses Firebase Authentication with JWT tokens. To authenticate:

1. Obtain a Firebase JWT token from your client application
2. Include the token in the `Authorization` header:

```http
Authorization: Bearer <firebase_jwt_token>
```

### Authentication Endpoints

- `GET /api/v1/auth/me/` - Get current user information
- `GET /api/v1/auth/verify/` - Verify token and get user data

## 👥 Roles and Permissions

### Admin
- Full access to all endpoints
- Can create, read, update, and delete any user
- Can view system statistics
- Can manage all resources

### Player
- Limited access to their own resources
- Can read their own information
- Can update their profile
- Cannot create or delete users
- Cannot access other users' information

## 🔌 Main Endpoints

### Users

```http
GET    /api/v1/users/           # List users (Admin: all, Player: only themselves)
POST   /api/v1/users/           # Create user (Admin only)
GET    /api/v1/users/{id}/      # Get specific user
PATCH  /api/v1/users/{id}/      # Update user
PUT    /api/v1/users/{id}/      # Update full user
DELETE /api/v1/users/{id}/      # Delete user (Admin only)
GET    /api/v1/users/stats/     # User statistics (Admin only)
```

### Request Example

```bash
# Get current user information
curl -X GET http://localhost:8000/api/v1/auth/me/ \
  -H "Authorization: Bearer <your_firebase_token>"

# Create new user (as Admin)
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer <your_firebase_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "new@example.com",
    "password": "password123",
    "first_name": "New",
    "last_name": "User",
    "role": "player"
  }'
```

## 🧪 Tests

Run all tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=apps --cov-report=html
```

Run specific tests:

```bash
pytest tests/test_users.py
pytest tests/test_permissions.py
pytest tests/test_api.py
```

## 🎨 Linters and Formatting

### Configure pre-commit hooks

```bash
pre-commit install
```

### Run linters manually

```bash
# Format code
make format

# Or individually:
black apps/ config/ tests/
isort apps/ config/ tests/

# Run linters
make lint

# Or individually:
flake8 apps/ config/
mypy apps/ config/
```

## 📁 Project Structure

```
backend.rtms/
├── apps/
│   ├── api/                    # API Endpoints
│   │   ├── views/
│   │   │   ├── auth_views.py   # Auth views
│   │   │   └── user_views.py   # User views
│   │   └── urls.py
│   ├── authentication/         # Firebase Authentication
│   │   ├── backends.py         # Auth backend
│   │   ├── permissions.py      # Permission classes
│   │   └── firebase_init.py    # Firebase initialization
│   └── users/                  # User model
│       ├── models.py           # Custom User model
│       ├── serializers.py      # DRF Serializers
│       └── admin.py            # Django Admin
├── config/
│   ├── settings/
│   │   ├── base.py            # Base settings
│   │   ├── dev.py             # Development settings
│   │   └── prod.py            # Production settings
│   ├── urls.py                # Main URLs
│   ├── wsgi.py
│   └── asgi.py
├── scripts/
│   ├── init_db.sh             # DB init script
│   └── create_test_users.py   # Create test users
├── tests/
│   ├── conftest.py            # pytest fixtures
│   ├── test_users.py          # User tests
│   ├── test_permissions.py    # Permission tests
│   └── test_api.py            # API tests
├── docker-compose.yml
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .pre-commit-config.yaml
├── .editorconfig
├── requirements.txt
├── pytest.ini
├── pyproject.toml
├── setup.cfg
├── Makefile
└── README.md
```

## 🔧 Useful Commands (Makefile)

```bash
make help           # See all available commands
make install        # Install dependencies
make migrate        # Run migrations
make run            # Run development server
make test           # Run tests
make lint           # Run linters
make format         # Format code
make clean          # Clean temporary files
make docker-build   # Build Docker image
make docker-up      # Start containers
make docker-down    # Stop containers
make shell          # Open Django shell
make dbshell        # Open PostgreSQL shell
```

## 🌐 Environment Variables

| Variable | Description | Default Value |
|----------|-------------|-------------------|
| `SECRET_KEY` | Django secret key | - |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hosts | `[]` |
| `DB_NAME` | Database name | `rtms_db` |
| `DB_USER` | PostgreSQL user | `rtms_user` |
| `DB_PASSWORD` | PostgreSQL password | `rtms_password` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase credentials | `firebase-credentials.json` |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `[]` |
| `DJANGO_SETTINGS_MODULE` | Settings module | `config.settings.dev` |

## 🚀 Production Deployment

### Important configurations:

1. **Environment variables**: Use `config.settings.prod`
2. **SECRET_KEY**: Generate a secure key
3. **DEBUG**: Set to `False`
4. **ALLOWED_HOSTS**: Configure with real domains
5. **Database**: Use PostgreSQL in production
6. **Static files**: Run `collectstatic`
7. **HTTPS**: Configure SSL/TLS
8. **Gunicorn**: Use as WSGI server

### Example with Gunicorn:

```bash
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 config.wsgi:application
```

## 📝 Additional Notes

### Asynchronous Support

The project is configured to support asynchronous views. To create an async view:

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from asgiref.sync import sync_to_async

@api_view(['GET'])
async def async_view(request):
    # Async code here
    result = await some_async_function()
    return Response({'result': result})
```

### Django Channels

The project includes Django Channels in dependencies for WebSocket support in the future. To use it, you'll need to configure ASGI routing.

## 🤝 Contributing

1. Fork the project
2. Create a branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📄 License

This project is under the MIT license.

## 📧 Contact

For questions or support, contact: [your-email@example.com]

---

**Developed with ❤️ using Django and Python**
