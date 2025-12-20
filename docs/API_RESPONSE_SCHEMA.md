# 📊 API Response Schema

This document describes the standard response schema implemented in the RTMS API.

## 🎯 Objective

Provide a consistent and predictable format for all API responses, facilitating frontend development and improving the developer experience.

## 📋 General Structure

All API responses follow a standard structure with the following fields:

### Main Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | boolean | ✅ | Indicates if the operation was successful |
| `message` | string | ✅ | Descriptive message of the operation |
| `data` | object/array/null | ❌ | Response data |
| `errors` | object | ❌ | Validation errors (only in errors) |
| `pagination` | object | ❌ | Pagination information (only in lists) |
| `meta` | object | ✅ | Response metadata |

## ✅ Successful Responses

### Simple Response (200 OK)

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "id": 1,
    "name": "Example",
    "created_at": "2024-01-20T15:45:00Z"
  },
  "meta": {
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "v1"
  }
}
```

### Creation Response (201 Created)

```json
{
  "success": true,
  "message": "Resource created successfully",
  "data": {
    "id": 1,
    "name": "New Resource",
    "created_at": "2024-01-20T15:45:00Z"
  },
  "meta": {
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "v1"
  }
}
```

### No Content Response (204 No Content)

```json
{
  "success": true,
  "message": "Resource deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "v1"
  }
}
```

## ❌ Error Responses

### Validation Error (400 Bad Request)

```json
{
  "success": false,
  "message": "Validation error in submitted data",
  "errors": {
    "email": ["This field is required."],
    "password": ["Password must be at least 8 characters long."]
  },
  "meta": {
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "v1",
    "error_code": "VALIDATION_ERROR"
  }
}
```

### Authentication Error (401 Unauthorized)

```json
{
  "success": false,
  "message": "You are not authenticated",
  "errors": null,
  "meta": {
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "v1",
    "error_code": "UNAUTHORIZED"
  }
}
```

### Permission Error (403 Forbidden)

```json
{
  "success": false,
  "message": "You do not have permission to perform this action",
  "errors": null,
  "meta": {
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "v1",
    "error_code": "FORBIDDEN"
  }
}
```

### Resource Not Found Error (404 Not Found)

```json
{
  "success": false,
  "message": "Resource not found",
  "errors": null,
  "meta": {
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "v1",
    "error_code": "NOT_FOUND"
  }
}
```

## 📄 Paginated Responses

```json
{
  "success": true,
  "message": "List retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "Item 1"
    },
    {
      "id": 2,
      "name": "Item 2"
    }
  ],
  "pagination": {
    "count": 100,
    "next": "http://api.example.com/users/?page=2",
    "previous": null,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "meta": {
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "v1"
  }
}
```

## 🔍 Metadata (meta)

The `meta` object contains additional information about the response:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp of the response |
| `version` | string | API version (currently "v1") |
| `error_code` | string | Specific error code (only in errors) |

## 📊 Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Data validation error |
| `UNAUTHORIZED` | User not authenticated |
| `FORBIDDEN` | No permission for the action |
| `NOT_FOUND` | Resource not found |
| `MISSING_REFRESH_TOKEN` | Missing refresh token |
| `INVALID_TOKEN` | Invalid token |
| `USER_NOT_FOUND` | User not found |
| `PLAYER_PROFILE_NOT_FOUND` | Player profile not found |
| `MISSING_USER_ID` | Missing user ID |
| `CANNOT_REMOVE_LAST_ADMIN` | Cannot remove the last administrator |

## 🛠️ Implementation

### In the Backend (Django)

```python
from apps.api.utils import APIResponse

# Successful response
return APIResponse.success(
    data=serializer.data,
    message="Operation successful"
)

# Error response
return APIResponse.error(
    message="Operation failed",
    errors=serializer.errors,
    error_code="VALIDATION_ERROR"
)

# Paginated response
return APIResponse.paginated(
    data=serializer.data,
    count=queryset.count(),
    page=page,
    page_size=page_size,
    next_url=next_url,
    previous_url=previous_url
)
```

### In the Frontend (JavaScript)

```javascript
// Standard response handling
const response = await fetch('/api/v1/users/');
const result = await response.json();

if (result.success) {
  // Successful operation
  console.log('Data:', result.data);
  console.log('Message:', result.message);
} else {
  // Error
  console.error('Error:', result.message);
  if (result.errors) {
    console.error('Validation errors:', result.errors);
  }
}
```

## 🎨 Schema Benefits

1. **Consistency**: All responses follow the same format
2. **Predictability**: Developers know what to expect
3. **Easy handling**: Frontend can handle all responses uniformly
4. **Debugging**: Metadata facilitates debugging
5. **Versioning**: Includes API version information
6. **Extensibility**: Easy to add new fields without breaking compatibility

## 📝 Migration Notes

- Existing responses have been updated to use this schema
- Frontend must be updated to handle the new format
- Existing tests must be updated to verify the new format
- Swagger documentation updates automatically
