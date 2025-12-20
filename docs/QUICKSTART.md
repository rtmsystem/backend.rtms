# 🚀 Quick Start

This guide will help you get the project running in less than 10 minutes.

## ⚡ Automatic Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd backend.rtms

# 2. Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Configure Firebase (download credentials)
# See: docs/FIREBASE_SETUP.md

# 4. Create test users
source venv/bin/activate
python scripts/create_test_users.py

# 5. Run server
python manage.py runserver
```

## 🐳 With Docker (Faster)

```bash
# 1. Clone the repository
git clone <repository-url>
cd backend.rtms

# 2. Create .env file
cp .env.example .env
# Edit .env with your values

# 3. Start services
docker-compose up -d

# 4. Run migrations
docker-compose exec web python manage.py migrate

# 5. Create superuser
docker-compose exec web python manage.py createsuperuser
```

Done! The API will be available at `http://localhost:8000`

## 📚 Important URLs

- **API**: http://localhost:8000/api/v1/
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **Admin**: http://localhost:8000/admin/

## 🔑 Test Users

If you ran `create_test_users.py`:

- **Admin**: admin@test.com / admin123
- **Player**: player@test.com / player123

## 🧪 Test the API

```bash
# With cURL (without Firebase authentication)
curl http://localhost:8000/swagger/

# View interactive documentation
# Open http://localhost:8000/swagger/ in your browser
```

## 📖 Next Step

Read the [complete documentation](README.md) for more details on:
- Firebase Authentication
- Available endpoints
- Integration examples
- Production deployment

## ❓ Common Problems

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Connection refused" (PostgreSQL)
```bash
# Option 1: Use Docker
docker-compose up -d db

# Option 2: Install local PostgreSQL
# Mac: brew install postgresql
# Ubuntu: sudo apt install postgresql
```

### "Firebase credentials not found"
Download your credentials from Firebase Console and save them as `firebase-credentials.json`.
See: [docs/FIREBASE_SETUP.md](docs/FIREBASE_SETUP.md)

---

Need help? Check the [full README](README.md) or open an issue.
