# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Backend RTMS is a Real-Time Management System for sports tournament management. It's a REST API built with Django 5.0 and Django REST Framework, using PostgreSQL, JWT authentication, and Cloudinary for media storage.

## Common Commands

```bash
# Development
make run              # Start dev server (0.0.0.0:8000)
make migrate          # Run makemigrations + migrate
make shell            # Django interactive shell

# Testing
pytest                         # Run all tests
pytest tests/test_users.py     # Run specific test file
pytest -k "test_name"          # Run tests matching pattern
pytest --cov=apps              # Run with coverage

# Code Quality
make format           # Run isort + black
make lint             # Run flake8 + mypy

# Docker
make docker-up        # Start containers
make docker-down      # Stop containers
```

## Architecture

### Project Structure

```
apps/
├── api/              # API configuration, mixins, utilities
├── authentication/   # Permissions (IsAdmin, IsAdminOrOwner)
├── users/            # Custom User model (email-based auth)
├── organizations/    # Company/entity management
├── players/          # PlayerProfile (independent from User)
├── tournaments/      # Tournament, Division, Group, Standing
├── matches/          # Match, Set models + scheduling
├── payments/         # Payment tracking per player/division
└── geographical/     # Country, City reference data

config/
├── settings/
│   ├── base.py       # Shared settings
│   ├── dev.py        # Development (DEBUG=True)
│   ├── test.py       # Testing (SQLite in-memory)
│   └── prod.py       # Production
└── urls.py           # Main URL routing
```

### Key Patterns

**Service Layer** (`apps/*/services.py`): Business logic lives in services, not views.
- `MatchCreationService`, `MatchSchedulingService`, `MatchScoringService`
- `GroupGenerationService`, `DivisionCompletionService`

**Standard Response Mixin** (`apps/api/mixins.py`): All ViewSets use `StandardModelViewSet` for consistent API responses with `success_response()`, `error_response()`, etc.

**Custom Permissions** (`apps/authentication/permissions.py`): `IsAdmin`, `IsAdminOrOwner`, `IsOrganizationAdmin`

**Validation** (`apps/*/validators.py`): Static validation methods like `MatchValidator.validate_match_creation_rules()`

### API Structure

All endpoints under `/api/v1/`:
- `auth/` - JWT login, refresh, logout, verify
- `users/` - User CRUD
- `organizations/` - Organization management
- `player-profiles/` - Player profiles
- `tournaments/` - Tournaments with nested divisions, involvements, groups
- `matches/` - Match creation, scheduling, scoring
- `geographical/` - Countries and cities
- Payment endpoints nested under tournaments/divisions

### Key Models

- **User**: Email-based (not username), roles: ADMIN/PLAYER
- **PlayerProfile**: Can exist independently from User, contains sport-specific data
- **Tournament**: Multiple formats (KNOCKOUT, ROUND_ROBIN, ROUND_ROBIN_KNOCKOUT)
- **TournamentDivision**: Categories within tournament (e.g., Men's Singles)
- **Match**: Supports singles/doubles, configurable sets and points, bracket structure

## Configuration

- Settings module: `DJANGO_SETTINGS_MODULE=config.settings.dev`
- Database: PostgreSQL (env vars: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`)
- Testing uses `config.settings.test` with SQLite in-memory

## Documentation

- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`
