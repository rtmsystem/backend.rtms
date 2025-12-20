# Deployment Guide

This guide will help you deploy the application in different production environments.

## 📋 Production Prerequisites

- Server with Python 3.11
- PostgreSQL 15+
- Nginx or similar (as reverse proxy)
- SSL/TLS Certificates
- Firebase Credentials
- Configured environment variables

## 🚀 Deployment on Linux Server (Ubuntu/Debian)

### 1. Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx supervisor
```

### 2. Configure PostgreSQL

```bash
# Create database and user
sudo -u postgres psql

CREATE DATABASE rtms_db;
CREATE USER rtms_user WITH PASSWORD 'your_secure_password';
ALTER ROLE rtms_user SET client_encoding TO 'utf8';
ALTER ROLE rtms_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE rtms_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE rtms_db TO rtms_user;
\q
```

### 3. Configure the Application

```bash
# Create system user
sudo useradd -m -s /bin/bash rtms

# Create directories
sudo mkdir -p /opt/rtms
sudo chown rtms:rtms /opt/rtms

# Switch to rtms user
sudo su - rtms

# Clone repository
cd /opt/rtms
git clone <repository-url> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 4. Configure Environment Variables

```bash
# Create .env file
nano /opt/rtms/.env
```

Content of `.env` for production:

```bash
# Django Settings
SECRET_KEY=your-randomly-generated-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=rtms_db
DB_USER=rtms_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Firebase
FIREBASE_CREDENTIALS_PATH=/opt/rtms/firebase-credentials.json

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Environment
DJANGO_SETTINGS_MODULE=config.settings.prod
```

### 5. Configure Firebase

```bash
# Copy Firebase credentials
nano /opt/rtms/firebase-credentials.json
# Paste the content of the Firebase JSON file

# Secure permissions
chmod 600 /opt/rtms/firebase-credentials.json
```

### 6. Run Migrations and Collect Static Files

```bash
source venv/bin/activate

# Migrations
python manage.py makemigrations
python manage.py migrate

# Static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

### 7. Configure Gunicorn

Create Gunicorn configuration file:

```bash
nano /opt/rtms/gunicorn_config.py
```

Content:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/opt/rtms/logs/gunicorn_access.log"
errorlog = "/opt/rtms/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "rtms_gunicorn"

# Server mechanics
daemon = False
pidfile = "/opt/rtms/gunicorn.pid"
```

### 8. Configure Supervisor

```bash
sudo nano /etc/supervisor/conf.d/rtms.conf
```

Content:

```ini
[program:rtms]
command=/opt/rtms/venv/bin/gunicorn config.wsgi:application -c /opt/rtms/gunicorn_config.py
directory=/opt/rtms
user=rtms
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/rtms/logs/supervisor.log
environment=
    DJANGO_SETTINGS_MODULE="config.settings.prod",
    PATH="/opt/rtms/venv/bin"
```

Start Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start rtms
sudo supervisorctl status rtms
```

### 9. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/rtms
```

Content:

```nginx
upstream rtms_server {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 100M;

    # Logging
    access_log /var/log/nginx/rtms_access.log;
    error_log /var/log/nginx/rtms_error.log;

    # Static files
    location /static/ {
        alias /opt/rtms/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/rtms/media/;
        expires 30d;
    }

    # Proxy to Gunicorn
    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://rtms_server;

        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

Activate configuration:

```bash
sudo ln -s /etc/nginx/sites-available/rtms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. Configure SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Automatic renewal
sudo certbot renew --dry-run
```

## 🐳 Deployment with Docker

### 1. Build Image

```bash
docker build -t rtms-backend:latest .
```

### 2. Docker Compose for Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: rtms_postgres
    restart: always
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - rtms_network

  web:
    image: rtms-backend:latest
    container_name: rtms_backend
    restart: always
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn --bind 0.0.0.0:8000 --workers 4 config.wsgi:application"
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    env_file:
      - .env.prod
    depends_on:
      - db
    networks:
      - rtms_network

  nginx:
    image: nginx:alpine
    container_name: rtms_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - web
    networks:
      - rtms_network

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  rtms_network:
    driver: bridge
```

### 3. Start Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## ☁️ Deployment on AWS (Elastic Beanstalk)

### 1. Prepare Application

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB
eb init -p python-3.11 rtms-backend

# Create environment
eb create rtms-prod --database.engine postgres
```

### 2. Configure Environment Variables

```bash
eb setenv SECRET_KEY=your-secret-key \
  DEBUG=False \
  DB_NAME=rtms_db \
  DB_USER=rtms_user \
  DB_PASSWORD=password \
  FIREBASE_CREDENTIALS_PATH=/opt/python/current/app/firebase-credentials.json
```

### 3. Deploy

```bash
eb deploy
```

## 🔧 Maintenance

### Update Application

```bash
# With supervisor
sudo su - rtms
cd /opt/rtms
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart rtms
```

### Monitor Logs

```bash
# Gunicorn Logs
tail -f /opt/rtms/logs/gunicorn_error.log

# Django Logs
tail -f /opt/rtms/logs/django.log

# Nginx Logs
sudo tail -f /var/log/nginx/rtms_error.log

# Supervisor Logs
sudo tail -f /var/log/supervisor/supervisord.log
```

### Database Backup

```bash
# Create backup
sudo -u postgres pg_dump rtms_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
sudo -u postgres psql rtms_db < backup_20240120_120000.sql
```

## 📊 Monitoring and Performance

### Recommended Tools

- **Sentry**: For error tracking
- **New Relic**: For performance monitoring
- **Prometheus + Grafana**: For metrics
- **ELK Stack**: For centralized logging

### Configure Sentry

```bash
pip install sentry-sdk
```

In `config/settings/prod.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

## 🔒 Security

### Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Unique and secure `SECRET_KEY`
- [ ] HTTPS configured correctly
- [ ] Firewall configured (only ports 80, 443, 22)
- [ ] PostgreSQL only accessible from localhost
- [ ] Credentials in environment variables
- [ ] Automatic backups configured
- [ ] Logging enabled
- [ ] Rate limiting configured
- [ ] CORS configured correctly

## 🆘 Troubleshooting

### Application does not start

```bash
# Check logs
sudo supervisorctl tail -f rtms stderr

# Check configuration
python manage.py check --deploy
```

### 502 Bad Gateway Errors

```bash
# Check that Gunicorn is running
sudo supervisorctl status rtms

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Database does not connect

```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Test connection
psql -U rtms_user -d rtms_db -h localhost
```

---

For more help, consult the Django documentation or open an issue in the repository.
