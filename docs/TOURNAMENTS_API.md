# Tournaments API Documentation

## Overview

The Tournaments API provides endpoints for managing sports tournaments and their divisions. This API allows organizations to create, manage, and publish tournaments with detailed information about events, participants, and locations.

## Base URL

```
/api/v1/organizations/{organization_id}/tournaments/
```

**Note:** All tournament endpoints require an `organization_id` in the URL path to specify which organization the tournaments belong to.

## Authentication

All endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Models

### Tournament

A tournament represents a sports competition with multiple divisions/events.

**Fields:**
- `id` (integer, read-only): Unique identifier
- `name` (string, required): Tournament name
- `description` (string, optional): Detailed description
- `contact_name` (string, required): Contact person name
- `contact_phone` (string, required): Contact phone number
- `contact_email` (email, required): Contact email address
- `start_date` (datetime, required): Tournament start date and time
- `end_date` (datetime, required): Tournament end date and time
- `registration_deadline` (datetime, required): Last date to register
- `address` (string, optional): Full address
- `street_number` (string, optional): Street or door number
- `street_location` (string, optional): Street or location details
- `city` (string, required): City name
- `state` (string, optional): State or province
- `country` (string, required): Country name
- `postal_code` (string, optional): Postal or ZIP code
- `organization` (integer, required): Organization ID
- `status` (string, required): Tournament status (draft, published, etc.)
- `is_active` (boolean): Whether the tournament is active
- `created_at` (datetime, read-only): Creation timestamp
- `updated_at` (datetime, read-only): Last update timestamp
- `created_by` (integer, read-only): User who created the tournament

**Computed Fields:**
- `division_count` (integer): Number of divisions in the tournament
- `is_registration_open` (boolean): Whether registration is currently open
- `is_upcoming` (boolean): Whether the tournament is upcoming
- `is_ongoing` (boolean): Whether the tournament is currently ongoing
- `organization_name` (string): Organization name
- `created_by_name` (string): Creator's full name

### TournamentDivision

A division represents a specific event within a tournament.

**Fields:**
- `id` (integer, read-only): Unique identifier
- `name` (string, required): Division/event name
- `description` (string, optional): Division description
- `format` (string, required): Tournament format (knockout, league, round_robin)
- `max_participants` (integer, optional): Maximum number of participants
- `gender` (string, required): Gender restriction (any, male, female)
- `participant_type` (string, required): Type of participants (single, team)
- `born_after` (date, optional): Age restriction (participants must be born after this date)
- `is_active` (boolean): Whether the division is active
- `created_at` (datetime, read-only): Creation timestamp
- `updated_at` (datetime, read-only): Last update timestamp

**Computed Fields:**
- `participant_count` (integer): Number of registered participants
- `is_full` (boolean): Whether the division is full
- `spots_remaining` (integer): Number of spots remaining

## Endpoints

### 1. List Tournaments

**GET** `/api/v1/organizations/{organization_id}/tournaments/`

Lists all tournaments for a specific organization.

**Query Parameters:**
- `search` (string, optional): Search in name, description, city, country
- `status` (string, optional): Filter by tournament status
- `city` (string, optional): Filter by city
- `country` (string, optional): Filter by country
- `is_active` (boolean, optional): Filter by active status

**Response:**
```json
{
  "count": 10,
  "next": "http://api.example.com/api/v1/tournaments/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Summer Tennis Championship",
      "organization_name": "Tennis Club",
      "status": "published",
      "start_date": "2024-06-01T09:00:00Z",
      "end_date": "2024-06-03T18:00:00Z",
      "city": "Lima",
      "country": "Peru",
      "division_count": 3,
      "is_registration_open": true,
      "is_upcoming": true,
      "is_ongoing": false,
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 2. Create Tournament

**POST** `/api/v1/organizations/{organization_id}/tournaments/`

Creates a new tournament for a specific organization.

**Request Body:**
```json
{
  "name": "Summer Tennis Championship",
  "description": "Annual summer tennis tournament for all skill levels",
  "contact_name": "John Doe",
  "contact_phone": "+1234567890",
  "contact_email": "john@example.com",
  "start_date": "2024-06-01T09:00:00Z",
  "end_date": "2024-06-03T18:00:00Z",
  "registration_deadline": "2024-05-25T23:59:59Z",
  "address": "123 Tennis Court St",
  "street_number": "123",
  "street_location": "Tennis Court St",
  "city": "Lima",
  "state": "Lima",
  "country": "Peru",
  "postal_code": "15001",
  "organization": 1,
  "status": "draft",
  "is_active": true,
  "divisions": [
    {
      "name": "Men's Singles",
      "description": "Men's singles competition",
      "format": "knockout",
      "max_participants": 32,
      "gender": "male",
      "participant_type": "single",
      "born_after": "2000-01-01",
      "is_active": true
    },
    {
      "name": "Women's Singles",
      "description": "Women's singles competition",
      "format": "knockout",
      "max_participants": 32,
      "gender": "female",
      "participant_type": "single",
      "born_after": "2000-01-01",
      "is_active": true
    }
  ]
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Summer Tennis Championship",
  "description": "Annual summer tennis tournament for all skill levels",
  "contact_name": "John Doe",
  "contact_phone": "+1234567890",
  "contact_email": "john@example.com",
  "start_date": "2024-06-01T09:00:00Z",
  "end_date": "2024-06-03T18:00:00Z",
  "registration_deadline": "2024-05-25T23:59:59Z",
  "address": "123 Tennis Court St",
  "street_number": "123",
  "street_location": "Tennis Court St",
  "city": "Lima",
  "state": "Lima",
  "country": "Peru",
  "postal_code": "15001",
  "organization": 1,
  "organization_name": "Tennis Club",
  "status": "draft",
  "is_active": true,
  "division_count": 2,
  "is_registration_open": false,
  "is_upcoming": true,
  "is_ongoing": false,
  "divisions": [
    {
      "id": 1,
      "name": "Men's Singles",
      "description": "Men's singles competition",
      "format": "knockout",
      "max_participants": 32,
      "gender": "male",
      "participant_type": "single",
      "born_after": "2000-01-01",
      "is_active": true,
      "participant_count": 0,
      "is_full": false,
      "spots_remaining": 32,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "created_by_name": "John Doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 3. Retrieve Tournament

**GET** `/api/v1/organizations/{organization_id}/tournaments/{id}/`

Retrieves a specific tournament by ID from a specific organization.

**Response:** Same as create tournament response.

### 4. Update Tournament

**PUT** `/api/v1/organizations/{organization_id}/tournaments/{id}/`

Updates a tournament. All fields must be provided.

**PATCH** `/api/v1/organizations/{organization_id}/tournaments/{id}/`

Partially updates a tournament. Only provided fields will be updated.

**Request Body:** Same as create tournament request body.

**Response:** Same as create tournament response.

### 5. Delete Tournament

**DELETE** `/api/v1/organizations/{organization_id}/tournaments/{id}/`

Deletes a tournament from a specific organization.

**Response:** 204 No Content

### 6. Publish Tournament

**POST** `/api/v1/organizations/{organization_id}/tournaments/{id}/publish/`

Publishes a tournament (changes status to published).

**Response:**
```json
{
  "id": 1,
  "name": "Summer Tennis Championship",
  "status": "published",
  // ... other tournament fields
}
```

### 7. Cancel Tournament

**POST** `/api/v1/organizations/{organization_id}/tournaments/{id}/cancel/`

Cancels a tournament (changes status to cancelled).

**Response:**
```json
{
  "id": 1,
  "name": "Summer Tennis Championship",
  "status": "cancelled",
  // ... other tournament fields
}
```

### 8. List Tournament Divisions

**GET** `/api/v1/organizations/{organization_id}/tournaments/{tournament_id}/divisions/`

Lists all divisions for a specific tournament.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Men's Singles",
    "description": "Men's singles competition",
    "format": "knockout",
    "max_participants": 32,
    "gender": "male",
    "participant_type": "single",
    "born_after": "2000-01-01",
    "is_active": true,
    "participant_count": 0,
    "is_full": false,
    "spots_remaining": 32,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

### 9. Create Tournament Division

**POST** `/api/v1/organizations/{organization_id}/tournaments/{tournament_id}/divisions/`

Creates a new division for a tournament.

**Request Body:**
```json
{
  "name": "Men's Doubles",
  "description": "Men's doubles competition",
  "format": "league",
  "max_participants": 16,
  "gender": "male",
  "participant_type": "team",
  "born_after": "2000-01-01",
  "is_active": true
}
```

**Response:** Same as list divisions response.

### 10. Retrieve Tournament Division

**GET** `/api/v1/organizations/{organization_id}/tournaments/{tournament_id}/divisions/{id}/`

Retrieves a specific division.

**Response:** Same as list divisions response.

### 11. Update Tournament Division

**PUT** `/api/v1/organizations/{organization_id}/tournaments/{tournament_id}/divisions/{id}/`

Updates a division.

**PATCH** `/api/v1/organizations/{organization_id}/tournaments/{tournament_id}/divisions/{id}/`

Partially updates a division.

**Request Body:** Same as create division request body.

**Response:** Same as list divisions response.

### 12. Delete Tournament Division

**DELETE** `/api/v1/organizations/{organization_id}/tournaments/{tournament_id}/divisions/{id}/`

Deletes a division.

**Response:** 204 No Content

### 13. Get Tournament Choices

**GET** `/api/v1/organizations/{organization_id}/tournaments/choices/`

Gets available choice options for tournament forms.

**Response:**
```json
{
  "formats": [
    {"value": "knockout", "label": "Knockout"},
    {"value": "league", "label": "League"},
    {"value": "round_robin", "label": "Round Robin"}
  ],
  "genders": [
    {"value": "any", "label": "Any"},
    {"value": "male", "label": "Male"},
    {"value": "female", "label": "Female"}
  ],
  "participant_types": [
    {"value": "single", "label": "Single"},
    {"value": "team", "label": "Team"}
  ],
  "statuses": [
    {"value": "draft", "label": "Draft"},
    {"value": "published", "label": "Published"},
    {"value": "registration_open", "label": "Registration Open"},
    {"value": "registration_closed", "label": "Registration Closed"},
    {"value": "in_progress", "label": "In Progress"},
    {"value": "completed", "label": "Completed"},
    {"value": "cancelled", "label": "Cancelled"}
  ]
}
```

### 14. Search Tournaments

**GET** `/api/v1/organizations/{organization_id}/tournaments/search/`

Advanced search for tournaments with multiple filters within a specific organization.

**Query Parameters:**
- `search` (string, optional): Search in name, description, city, country
- `status` (string, optional): Filter by tournament status
- `city` (string, optional): Filter by city
- `country` (string, optional): Filter by country
- `is_active` (boolean, optional): Filter by active status

**Response:** Same as list tournaments response.

## Validation Rules

### Tournament Validation

1. **Required Fields:** name, contact_name, contact_phone, contact_email, start_date, end_date, registration_deadline, city, country, organization
2. **Email Format:** contact_email must be a valid email address
3. **Date Validation:** 
   - registration_deadline must be before start_date
   - end_date must be after start_date
4. **Organization Access:** User must be an administrator of the organization

### Division Validation

1. **Required Fields:** name, format, participant_type
2. **Max Participants:** Must be a positive integer if specified
3. **Unique Name:** Division name must be unique within the tournament
4. **Tournament Access:** User must have access to the parent tournament

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "detail": "A server error occurred."
}
```

## Status Codes

- `draft`: Tournament is being created/edited
- `published`: Tournament is published and visible
- `registration_open`: Registration is open for participants
- `registration_closed`: Registration deadline has passed
- `in_progress`: Tournament is currently running
- `completed`: Tournament has finished
- `cancelled`: Tournament has been cancelled

## Permissions

- **Create Tournament:** User must be an administrator of at least one organization
- **View Tournament:** User must be an administrator of the tournament's organization
- **Edit Tournament:** User must be an administrator of the tournament's organization
- **Delete Tournament:** User must be an administrator of the tournament's organization
- **Publish/Cancel Tournament:** User must be an administrator of the tournament's organization

## Examples

### Creating a Complete Tournament

```bash
curl -X POST "http://localhost:8000/api/v1/organizations/1/tournaments/" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Spring Badminton Championship",
    "description": "Annual spring badminton tournament",
    "contact_name": "Jane Smith",
    "contact_phone": "+1234567890",
    "contact_email": "jane@example.com",
    "start_date": "2024-04-01T09:00:00Z",
    "end_date": "2024-04-03T18:00:00Z",
    "registration_deadline": "2024-03-25T23:59:59Z",
    "city": "Lima",
    "country": "Peru",
    "status": "draft",
    "divisions": [
      {
        "name": "Men\'s Singles",
        "format": "knockout",
        "max_participants": 32,
        "gender": "male",
        "participant_type": "single"
      }
    ]
  }'
```

### Publishing a Tournament

```bash
curl -X POST "http://localhost:8000/api/v1/organizations/1/tournaments/1/publish/" \
  -H "Authorization: Bearer <your_jwt_token>"
```

### Searching Tournaments

```bash
curl -X GET "http://localhost:8000/api/v1/organizations/1/tournaments/search/?search=tennis&status=published&city=Lima" \
  -H "Authorization: Bearer <your_jwt_token>"
```
