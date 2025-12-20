# Contribution Guide

Thank you for your interest in contributing to RTMS Backend! This guide will help you get started.

## 📋 Code of Conduct

- Be respectful and professional
- Accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other members

## 🚀 How to Contribute

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/your-username/backend.rtms.git
cd backend.rtms

# Add the original repository as remote
git remote add upstream https://github.com/original/backend.rtms.git
```

### 2. Create a Branch

```bash
# Update your main
git checkout main
git pull upstream main

# Create a new branch
git checkout -b feature/new-feature
# or
git checkout -b fix/bug-fix
```

### 3. Configure Development Environment

```bash
# Install dependencies
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Configure database
python manage.py migrate
```

### 4. Make Changes

- Write clean and readable code
- Follow Python conventions (PEP 8)
- Add docstrings to functions and classes
- Add type hints when possible

### 5. Run Tests

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_users.py

# With coverage
pytest --cov=apps --cov-report=html
```

### 6. Run Linters

```bash
# Format code
make format

# Or manually:
black apps/ config/ tests/
isort apps/ config/ tests/

# Run linters
make lint

# Or manually:
flake8 apps/ config/
mypy apps/ config/
```

### 7. Commit

```bash
# Add changes
git add .

# Commit with descriptive message
git commit -m "feat: add new feature X"
```

#### Commit Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description

More detailed description if necessary.

Fixes #123
```

**Commit types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes (do not affect code)
- `refactor`: Code refactoring
- `test`: Add or modify tests
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat(users): add endpoint to change password"
git commit -m "fix(auth): fix expired token validation"
git commit -m "docs: update README with new endpoints"
git commit -m "test(api): add tests for users endpoint"
```

### 8. Push and Pull Request

```bash
# Push to your fork
git push origin feature/new-feature

# Create Pull Request on GitHub
# Go to your fork on GitHub and click "New Pull Request"
```

## 📝 Style Guides

### Python

We follow [PEP 8](https://pep8.org/) with some particularities:

- Maximum line length: 100 characters
- Use double quotes for strings
- Sorted imports with isort
- Type hints in public functions

```python
from typing import Optional

def create_user(
    email: str,
    password: str,
    role: str = 'player'
) -> Optional[User]:
    """
    Creates a new user in the system.
    
    Args:
        email: User email
        password: Plain text password
        role: User role (admin or player)
    
    Returns:
        Created user instance or None if it fails
    
    Raises:
        ValidationError: If data is invalid
    """
    # Implementation
    pass
```

### Django

- Use efficient QuerySets (select_related, prefetch_related)
- Validate data in serializers and forms
- Use transactions when necessary
- Appropriate logging

```python
# Good
users = User.objects.select_related('profile').filter(is_active=True)

# Avoid
users = User.objects.all()
for user in users:
    profile = user.profile  # N+1 queries
```

### Django REST Framework

- One serializer per operation if necessary
- Validations in serializers
- Granular permissions
- Document with swagger_auto_schema

```python
from drf_yasg.utils import swagger_auto_schema

@swagger_auto_schema(
    operation_description="Endpoint description",
    responses={200: UserSerializer()}
)
def get(self, request):
    pass
```

## 🧪 Tests

### Test Structure

```python
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model."""
    
    def test_create_user(self):
        """Test verifying user creation."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
```

### Minimum Coverage

- New features: 80% minimum coverage
- Critical code: 90% minimum coverage
- Bugs: Add test reproducing the bug before fixing it

## 📚 Documentation

### Code

- Docstrings in all public functions
- Comments for complex logic
- Type hints

### README and Docs

- Update README if you add features
- Add usage examples
- Update CHANGELOG.md

### API

- Document with swagger_auto_schema
- Include request/response examples
- Document error codes

## 🐛 Report Bugs

### Before Reporting

1. Verify that a similar issue does not exist
2. Make sure to use the latest version
3. Try to reproduce the bug

### Information to Include

```markdown
**Bug Description**
Clear and concise description of the bug.

**To Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python: [e.g. 3.11]
 - Django: [e.g. 5.0.1]

**Additional Information**
Any other context about the problem.
```

## ✨ Suggest Improvements

```markdown
**Is your suggestion related to a problem?**
Clear description of the problem.

**Describe the solution you would like**
Clear description of what you want to happen.

**Alternatives considered**
Other solutions or features you considered.

**Additional context**
Any other context or screenshots.
```

## 📋 Pull Request Checklist

Before submitting a PR, make sure:

- [ ] The code follows the project style
- [ ] I have performed a self-review of my code
- [ ] I have commented on areas difficult to understand
- [ ] I have updated the documentation
- [ ] My changes do not generate new warnings
- [ ] I have added tests that prove my fix/feature
- [ ] New and existing tests pass locally
- [ ] Dependent changes have been merged
- [ ] I have updated CHANGELOG.md

## 🔄 Review Process

1. **Automatic Review**: GitHub Actions runs tests and linters
2. **Code Review**: A maintainer will review your code
3. **Requested Changes**: If there are comments, update your PR
4. **Approval**: When everything is fine, the PR will be merged

## 💡 Tips

- Keep PRs small and focused
- One PR = One feature or fix
- Respond to comments quickly
- Be patient and polite

## 🎓 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [pytest Documentation](https://docs.pytest.org/)

## ❓ Questions

If you have questions, you can:

1. Open a [Discussion](https://github.com/user/repo/discussions)
2. Open an [Issue](https://github.com/user/repo/issues)
3. Contact the maintainers

---

Thanks for contributing! 🎉
