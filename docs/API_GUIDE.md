# API Usage Guide

This guide provides detailed examples of how to consume the RTMS API.

## 📋 Table of Contents

- [Response Schema](#response-schema)
- [Authentication](#authentication)
- [User Endpoints](#user-endpoints)
- [Error Handling](#error-handling)
- [Pagination](#pagination)
- [Filtering and Search](#filtering-and-search)
- [Rate Limiting](#rate-limiting)
- [Integration Examples](#integration-examples)

## 📊 Response Schema

All API responses follow a consistent standard schema to facilitate frontend handling.

### ✅ Successful Responses

```json
{
  "success": true,
  "message": "Successful operation",
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "v1"
  }
}
```

### ❌ Error Responses

```json
{
  "success": false,
  "message": "Error description",
  "errors": {
    "field_name": ["Specific field error"]
  },
  "meta": {
    "timestamp": "2024-01-20T15:45:00Z",
    "version": "v1",
    "error_code": "VALIDATION_ERROR"
  }
}
```

### 📄 Paginated Responses

```json
{
  "success": true,
  "message": "List retrieved successfully",
  "data": [...],
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

### 🔍 Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indicates if the operation was successful |
| `message` | string | Descriptive message of the operation |
| `data` | object/array | Response data (can be null) |
| `errors` | object | Validation errors (only in error responses) |
| `pagination` | object | Pagination information (only in lists) |
| `meta` | object | Response metadata |
| `meta.timestamp` | string | ISO 8601 timestamp of the response |
| `meta.version` | string | API Version |
| `meta.error_code` | string | Specific error code (only in errors) |

## 🔐 Authentication

All endpoints (except documentation) require authentication via Firebase JWT token.

### Authentication Header

```http
Authorization: Bearer <firebase_jwt_token>
```

### Get Token

From your client application, authenticate with Firebase and get the token:

```javascript
// JavaScript/TypeScript
import { getAuth } from 'firebase/auth';

const auth = getAuth();
const user = auth.currentUser;
const token = await user.getIdToken();

// Use this token in your requests
```

### Authenticated Request Example

```bash
curl -X GET http://localhost:8000/api/v1/auth/me/ \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5..."
```

## 👤 User Endpoints

### 1. Get Current User

Gets the authenticated user's information.

**Endpoint**: `GET /api/v1/auth/me/`

**Successful Response** (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "role": "player",
  "is_admin": false,
  "is_player": true,
  "is_active": true,
  "date_joined": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T15:45:00Z"
}
```

**JavaScript Example**:
```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/me/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const userData = await response.json();
```

### 2. Verify Token

Verifies that the token is valid and returns user information.

**Endpoint**: `GET /api/v1/auth/verify/`

**Successful Response** (200):
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "player"
  },
  "message": "Valid token"
}
```

### 3. List Users

Lists users according to the authenticated user's role.

**Endpoint**: `GET /api/v1/users/`

**Permissions**:
- **Admin**: Sees all users
- **Player**: Only sees their own profile

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Page size (default: 20, max: 100)

**Successful Response** (200):
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/v1/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "email": "admin@example.com",
      "first_name": "Admin",
      "last_name": "User",
      "full_name": "Admin User",
      "role": "admin",
      "is_admin": true,
      "is_player": false,
      "is_active": true,
      "date_joined": "2024-01-01T00:00:00Z",
      "last_login": "2024-01-20T10:00:00Z"
    }
  ]
}
```

**cURL Example**:
```bash
curl -X GET "http://localhost:8000/api/v1/users/?page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

### 4. Get Specific User

Gets the details of a user by ID.

**Endpoint**: `GET /api/v1/users/{id}/`

**Permissions**:
- **Admin**: Can view any user
- **Player**: Can only view their own profile

**Successful Response** (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "role": "player",
  "is_admin": false,
  "is_player": true,
  "is_active": true,
  "date_joined": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T15:45:00Z"
}
```

### 5. Create User

Creates a new user (Admin only).

**Endpoint**: `POST /api/v1/users/`

**Permissions**: Admin only

**Body**:
```json
{
  "email": "new@example.com",
  "password": "password123",
  "first_name": "New",
  "last_name": "User",
  "role": "player"
}
```

**Successful Response** (201):
```json
{
  "id": 5,
  "email": "new@example.com",
  "first_name": "New",
  "last_name": "User",
  "full_name": "New User",
  "role": "player",
  "is_admin": false,
  "is_player": true,
  "is_active": true,
  "date_joined": "2024-01-20T16:00:00Z",
  "last_login": null
}
```

**JavaScript Example**:
```javascript
const response = await fetch('http://localhost:8000/api/v1/users/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'new@example.com',
    password: 'password123',
    first_name: 'New',
    last_name: 'User',
    role: 'player'
  })
});
const newUser = await response.json();
```

### 6. Update User

Updates a user's information.

**Endpoint**: `PATCH /api/v1/users/{id}/`

**Permissions**:
- **Admin**: Can update any user (including role)
- **Player**: Can only update their own profile (without changing role)

**Body (Player)**:
```json
{
  "first_name": "Updated John",
  "last_name": "New Doe"
}
```

**Body (Admin)**:
```json
{
  "first_name": "Updated John",
  "last_name": "New Doe",
  "role": "admin",
  "is_active": true
}
```

**Successful Response** (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Updated John",
  "last_name": "New Doe",
  "full_name": "Updated John New Doe",
  "role": "player",
  "is_admin": false,
  "is_player": true,
  "is_active": true,
  "date_joined": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T15:45:00Z"
}
```

**cURL Example**:
```bash
curl -X PATCH http://localhost:8000/api/v1/users/1/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Updated John"}'
```

### 7. Delete User

Deletes a user (Admin only).

**Endpoint**: `DELETE /api/v1/users/{id}/`

**Permissions**: Admin only

**Successful Response** (204): No content

**cURL Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/users/5/ \
  -H "Authorization: Bearer <token>"
```

### 8. User Statistics

Gets general user statistics (Admin only).

**Endpoint**: `GET /api/v1/users/stats/`

**Permissions**: Admin only

**Successful Response** (200):
```json
{
  "total_users": 100,
  "total_admins": 5,
  "total_players": 95,
  "active_users": 87
}
```

## ⚠️ Error Handling

The API uses standard HTTP status codes and returns errors in JSON format.

### Status Codes

| Code | Description |
|--------|-------------|
| 200 | OK - Successful request |
| 201 | Created - Resource created successfully |
| 204 | No Content - Successful request without content |
| 400 | Bad Request - Invalid data |
| 401 | Unauthorized - Not authenticated |
| 403 | Forbidden - No permissions |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

### Error Format

```json
{
  "detail": "Descriptive error message"
}
```

Or for validation errors:

```json
{
  "email": ["This field is required."],
  "password": ["Password must have at least 8 characters."]
}
```

### Error Examples

**401 - Unauthenticated**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 - Forbidden**:
```json
{
  "detail": "Only administrators have permission to perform this action."
}
```

**404 - Not Found**:
```json
{
  "detail": "Not found."
}
```

**400 - Validation**:
```json
{
  "email": ["Enter a valid email address."],
  "password": ["This field cannot be blank."]
}
```

## 📄 Pagination

Endpoints returning lists use automatic pagination.

### Parameters

- `page`: Page number (default: 1)
- `page_size`: Page size (default: 20, max: 100)

### Response Format

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/users/?page=3",
  "previous": "http://localhost:8000/api/v1/users/?page=1",
  "results": [...]
}
```

### Example

```bash
# First page (20 items)
curl -X GET "http://localhost:8000/api/v1/users/?page=1" \
  -H "Authorization: Bearer <token>"

# Second page with 50 items
curl -X GET "http://localhost:8000/api/v1/users/?page=2&page_size=50" \
  -H "Authorization: Bearer <token>"
```

## 🚦 Rate Limiting

The API implements rate limiting to prevent abuse.

### Limits

- **Anonymous Users**: 100 requests/hour
- **Authenticated Users**: 1000 requests/hour

### Rate Limit Headers

Not currently implemented, but you can add custom headers.

### Response when limit exceeded

**Status**: 429 Too Many Requests

```json
{
  "detail": "Request limit exceeded. Please try again later."
}
```

## 💻 Integration Examples

### JavaScript/TypeScript (Fetch API)

```javascript
class RTMSClient {
  constructor(baseURL, firebaseAuth) {
    this.baseURL = baseURL;
    this.auth = firebaseAuth;
  }

  async getToken() {
    const user = this.auth.currentUser;
    if (!user) throw new Error('User not authenticated');
    return await user.getIdToken();
  }

  async request(endpoint, options = {}) {
    const token = await this.getToken();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request error');
    }

    return response.status === 204 ? null : await response.json();
  }

  // User methods
  async getCurrentUser() {
    return this.request('/api/v1/auth/me/');
  }

  async listUsers(page = 1, pageSize = 20) {
    return this.request(`/api/v1/users/?page=${page}&page_size=${pageSize}`);
  }

  async createUser(userData) {
    return this.request('/api/v1/users/', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  async updateUser(userId, userData) {
    return this.request(`/api/v1/users/${userId}/`, {
      method: 'PATCH',
      body: JSON.stringify(userData)
    });
  }

  async deleteUser(userId) {
    return this.request(`/api/v1/users/${userId}/`, {
      method: 'DELETE'
    });
  }
}

// Usage
const client = new RTMSClient('http://localhost:8000', getAuth());

// Get current user
const user = await client.getCurrentUser();
console.log('Current user:', user);

// List users
const users = await client.listUsers();
console.log('Users:', users.results);
```

### Python (requests)

```python
import requests
from typing import Optional, Dict, Any

class RTMSClient:
    def __init__(self, base_url: str, firebase_token: str):
        self.base_url = base_url
        self.token = firebase_token
        self.headers = {
            'Authorization': f'Bearer {firebase_token}',
            'Content-Type': 'application/json'
        }

    def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None
    ) -> Any:
        url = f"{self.base_url}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json() if response.content else None

    def get_current_user(self) -> Dict:
        return self._request('GET', '/api/v1/auth/me/')

    def list_users(self, page: int = 1, page_size: int = 20) -> Dict:
        return self._request(
            'GET', 
            f'/api/v1/users/?page={page}&page_size={page_size}'
        )

    def create_user(self, user_data: Dict) -> Dict:
        return self._request('POST', '/api/v1/users/', data=user_data)

    def update_user(self, user_id: int, user_data: Dict) -> Dict:
        return self._request(
            'PATCH', 
            f'/api/v1/users/{user_id}/', 
            data=user_data
        )

    def delete_user(self, user_id: int) -> None:
        return self._request('DELETE', f'/api/v1/users/{user_id}/')

# Usage
client = RTMSClient('http://localhost:8000', 'your_firebase_token')

# Get current user
user = client.get_current_user()
print(f"Current user: {user['email']}")

# List users
users = client.list_users(page=1, page_size=10)
print(f"Total users: {users['count']}")
```

### Custom React Hook

```typescript
import { useState, useEffect } from 'react';
import { getAuth } from 'firebase/auth';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: 'admin' | 'player';
}

export function useRTMSAPI() {
  const [token, setToken] = useState<string | null>(null);
  const auth = getAuth();
  const baseURL = 'http://localhost:8000';

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged(async (user) => {
      if (user) {
        const idToken = await user.getIdToken();
        setToken(idToken);
      } else {
        setToken(null);
      }
    });

    return unsubscribe;
  }, []);

  const request = async (endpoint: string, options: RequestInit = {}) => {
    if (!token) throw new Error('Not authenticated');

    const response = await fetch(`${baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request error');
    }

    return response.status === 204 ? null : await response.json();
  };

  return {
    getCurrentUser: () => request('/api/v1/auth/me/'),
    listUsers: (page = 1, pageSize = 20) => 
      request(`/api/v1/users/?page=${page}&page_size=${pageSize}`),
    createUser: (userData: Partial<User>) => 
      request('/api/v1/users/', {
        method: 'POST',
        body: JSON.stringify(userData),
      }),
    updateUser: (userId: number, userData: Partial<User>) => 
      request(`/api/v1/users/${userId}/`, {
        method: 'PATCH',
        body: JSON.stringify(userData),
      }),
    deleteUser: (userId: number) => 
      request(`/api/v1/users/${userId}/`, {
        method: 'DELETE',
      }),
  };
}

// Component Usage
function UserProfile() {
  const api = useRTMSAPI();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.getCurrentUser().then(setUser).catch(console.error);
  }, []);

  return user ? (
    <div>
      <h1>{user.first_name} {user.last_name}</h1>
      <p>{user.email}</p>
      <p>Role: {user.role}</p>
    </div>
  ) : (
    <p>Loading...</p>
  );
}
```

## 📚 Additional Resources

- [Swagger Documentation](http://localhost:8000/swagger/)
- [ReDoc Documentation](http://localhost:8000/redoc/)
- [Firebase Authentication Docs](https://firebase.google.com/docs/auth)

---

Have questions? Check the full documentation or open an issue in the repository.
