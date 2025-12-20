#!/usr/bin/env python3
# -*- coding: utf-8 -*-

with open('.cursorrules', 'r', encoding='utf-8') as f:
    content = f.read()

old_section = """### 5. Custom Exceptions

Define business-specific exceptions:

```python
# exceptions.py

class BusinessLogicError(Exception):
    \"\"\"Base exception for business logic errors.\"\"\"
    pass

class ResourceNotFoundError(BusinessLogicError):
    \"\"\"Raised when a resource cannot be found.\"\"\"
    pass

class DuplicateResourceError(BusinessLogicError):
    \"\"\"Raised when attempting to create a duplicate resource.\"\"\"
    pass

class InsufficientPermissionsError(BusinessLogicError):
    \"\"\"Raised when user lacks required permissions.\"\"\"
    pass
```"""

new_section = """### 5. Custom Exceptions with Error Codes for i18n

**CRITICAL**: All business logic exceptions MUST include an `error_code` for frontend internationalization support.

#### Base Exception Pattern

Create a base exception class that includes `error_code`:

```python
# exceptions.py
from django.core.exceptions import ValidationError
from typing import Optional, Dict, Any


class BusinessLogicError(ValidationError):
    \"\"\"Base exception for business logic errors with error code.\"\"\"
    
    def __init__(
        self,
        message: str,
        error_code: str,
        errors: Optional[Dict[str, Any]] = None
    ) -> None:
        self.error_code = error_code
        self.message = message
        super().__init__(message)
        if errors:
            self.error_dict = errors
```

#### Specific Exception Classes

Each specific exception should:
1. Inherit from the base exception
2. Define a unique, descriptive `error_code` in UPPER_SNAKE_CASE
3. Include a descriptive message
4. Optionally include structured errors dict

```python
# exceptions.py

class InsufficientApprovedPlayersError(BusinessLogicError):
    \"\"\"Raised when division has less than 2 approved players.\"\"\"
    
    def __init__(self, approved_count: int) -> None:
        message = (
            f'Division cannot be published. '
            f'It must have at least 2 approved players. '
            f'Currently has {approved_count}.'
        )
        super().__init__(
            message=message,
            error_code="ERROR_LESS_TWO_INVOLVEMENT",
            errors={'division': [message]}
        )


class HasPendingInvolvementsError(BusinessLogicError):
    \"\"\"Raised when division has pending involvements.\"\"\"
    
    def __init__(self, pending_count: int) -> None:
        message = (
            f'Division cannot be published. '
            f'It must have no pending players. '
            f'There are {pending_count} pending involvements.'
        )
        super().__init__(
            message=message,
            error_code="ERROR_PENDING_INVOLVEMENTS",
            errors={'division': [message]}
        )


class ResourceAlreadyPublishedError(BusinessLogicError):
    \"\"\"Raised when trying to publish an already published resource.\"\"\"
    
    def __init__(self) -> None:
        message = 'This resource is already published and closed.'
        super().__init__(
            message=message,
            error_code="ERROR_RESOURCE_ALREADY_PUBLISHED",
            errors={'resource': [message]}
        )


class RegistrationClosedError(BusinessLogicError):
    \"\"\"Raised when trying to register in a closed resource.\"\"\"
    
    def __init__(self) -> None:
        message = 'Registration for this resource is closed. No new registrations are allowed.'
        super().__init__(
            message=message,
            error_code="ERROR_REGISTRATION_CLOSED",
            errors={'resource': [message]}
        )
```

#### Using Exceptions in Models

Models should raise these exceptions in validation methods:

```python
# models.py
from .exceptions import (
    InsufficientApprovedPlayersError,
    HasPendingInvolvementsError,
    ResourceAlreadyPublishedError
)

class Resource(models.Model):
    # ... fields ...
    
    def publish(self, user=None):
        \"\"\"Publish the resource.\"\"\"
        from .exceptions import (
            InsufficientApprovedPlayersError,
            HasPendingInvolvementsError,
            ResourceAlreadyPublishedError
        )
        
        # Verificar si ya está publicada
        if self.is_published:
            raise ResourceAlreadyPublishedError()
        
        # Validar mínimo 2 jugadores aprobados
        if self.approved_count < 2:
            raise InsufficientApprovedPlayersError(self.approved_count)
        
        # Validar que no haya involvements pendientes
        if self.has_pending_involvements:
            pending_count = self.involvements.filter(
                status=InvolvementStatus.PENDING
            ).count()
            raise HasPendingInvolvementsError(pending_count)
        
        self.is_published = True
        self.published_at = timezone.now()
        if user:
            self.published_by = user
        self.save(update_fields=['is_published', 'published_at', 'published_by', 'updated_at'])
```

#### Handling Exceptions in Views

Views MUST catch business logic exceptions and extract the `error_code`:

```python
# views.py
from .exceptions import BusinessLogicError
from apps.api.utils import APIResponse

@api_view([\"POST\"])
@permission_classes([IsAuthenticated])
def publish_resource(request, resource_id):
    \"\"\"Publish a resource.\"\"\"
    try:
        resource = Resource.objects.get(pk=resource_id)
        resource.publish(user=request.user)
        
        serializer = ResourceSerializer(resource)
        return APIResponse.success(
            data=serializer.data,
            message=\"Resource published successfully\"
        )
    
    except BusinessLogicError as e:
        # Capturar excepciones de negocio con error_code
        return APIResponse.validation_error(
            errors=e.error_dict if hasattr(e, 'error_dict') else {'error': [str(e)]},
            message=str(e),
            error_code=e.error_code  # CRITICAL: Pasar el error_code al frontend
        )
    
    except Resource.DoesNotExist:
        return APIResponse.not_found(
            message=\"Resource not found\",
            error_code=\"RESOURCE_NOT_FOUND\"
        )
    
    except Exception as e:
        logger.exception(\"Unexpected error publishing resource\")
        return APIResponse.error(
            message=\"An unexpected error occurred\",
            error_code=\"RESOURCE_PUBLISH_ERROR\",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

#### Error Code Naming Convention

1. **Format**: `ERROR_<DESCRIPTIVE_NAME>` or `<ACTION>_<RESOURCE>_<CONDITION>`
2. **Examples**:
   - `ERROR_LESS_TWO_INVOLVEMENT` - Less than 2 involvements
   - `ERROR_PENDING_INVOLVEMENTS` - Has pending involvements
   - `ERROR_DIVISION_ALREADY_PUBLISHED` - Division already published
   - `ERROR_REGISTRATION_CLOSED` - Registration is closed
   - `RESOURCE_NOT_FOUND` - Resource not found
   - `FORBIDDEN_ACTION` - Permission denied
3. **Be specific**: Use descriptive names that clearly indicate the error condition
4. **Be consistent**: Follow the same pattern across the entire application

#### Error Code Checklist

When creating a new exception:
- [ ] Exception inherits from `BusinessLogicError` (or similar base)
- [ ] `error_code` is defined in UPPER_SNAKE_CASE
- [ ] `error_code` is descriptive and unique
- [ ] Exception includes a clear message
- [ ] Exception optionally includes structured `errors` dict
- [ ] View catches exception and passes `error_code` to `APIResponse`
- [ ] Error code is documented for frontend team
"""

if old_section in content:
    content = content.replace(old_section, new_section)
    with open('.cursorrules', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replacement successful')
else:
    print('Section not found exactly. Trying line-based approach...')
    lines = content.split('\n')
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if line.strip() == '### 5. Custom Exceptions':
            start_idx = i
        elif start_idx is not None and line.strip() == '---' and i > start_idx + 5:
            end_idx = i
            break
    
    if start_idx is not None and end_idx is not None:
        new_lines = lines[:start_idx] + new_section.split('\n') + lines[end_idx:]
        with open('.cursorrules', 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print('Replacement successful using line-based approach')
    else:
        print(f'Could not find section boundaries. start_idx={start_idx}, end_idx={end_idx}')

