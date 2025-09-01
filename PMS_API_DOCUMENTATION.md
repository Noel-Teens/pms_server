# Paper Management System API Documentation

This document provides comprehensive documentation for the Paper Management System API endpoints.

## Table of Contents

1. [Authentication](#authentication)
2. [API Endpoints](#api-endpoints)
   - [Auth API](#auth-api)
   - [Admin API](#admin-api)
   - [Paper Management API](#paper-management-api)
3. [Models](#models)
4. [Error Handling](#error-handling)

## Authentication

The API uses JWT (JSON Web Token) authentication. Most endpoints require authentication.

### Token Acquisition

**Endpoint**: `POST /auth/login/`

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response**:
```json
{
  "refresh": "string",
  "access": "string",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "role": "string",
    "status": "string"
  }
}
```

### Google Authentication

**Endpoint**: `POST /auth/google/`

**Request Body**:
```json
{
  "id_token": "string"
}
```

**Response**: Same as regular login

## API Endpoints

### Auth API

#### Register User

**Endpoint**: `POST /auth/register/`

**Permission**: AllowAny

**Request Body**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "string" // Optional, defaults to "RESEARCHER"
}
```

**Response**:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "role": "string"
  }
}
```

#### Get Current User

**Endpoint**: `GET /auth/me/`

**Permission**: IsAuthenticated

**Response**:
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "role": "string",
  "status": "string"
}
```

### Admin API

#### Create User

**Endpoint**: `POST /admin_app/createusers/`

**Permission**: IsAuthenticated, IsAdmin

**Request Body**:
```json
{
  "username": "string",
  "email": "string",
  "role": "string",
  "status": "string"
}
```

**Response**: User object

#### Update User Status

**Endpoint**: `PATCH /admin_app/updateusers/<username>/status/`

**Permission**: IsAuthenticated, IsAdmin

**Request Body**:
```json
{
  "status": "string" // One of: "ACTIVE", "FROZEN", "INACTIVE"
}
```

**Response**: User object

#### List Users

**Endpoint**: `GET /admin_app/users/`

**Permission**: IsAuthenticated, IsAdmin

**Response**: Array of User objects (excluding admins)

#### Get User Detail

**Endpoint**: `GET /admin_app/users/<user_id>/`

**Permission**: IsAuthenticated, IsAdmin

**Response**: User object

#### View Paperwork File

**Endpoint**: `GET /admin_app/paperworks/<paperwork_id>/versions/<version_no>/<file_type>/view/`

**Permission**: IsAuthenticated, IsAdmin

**Parameters**:
- `paperwork_id`: UUID of the paperwork
- `version_no`: Integer version number
- `file_type`: String, one of: "pdf", "latex", "python", "docx"

**Response**: File content with appropriate content type

**Notes**: 
- Allows administrators to view files directly in the browser without downloading
- Returns 404 if the version or file doesn't exist
- Returns 400 for invalid file types

#### Assign Paper Work

**Endpoint**: `POST /admin_app/paperworks/`

**Permission**: IsAuthenticated, IsAdmin

**Request Body**:
```json
{
  "title": "string",
  "researcher_id": "uuid",
  "deadline": "datetime" // Optional
}
```

**Response**: PaperWork object

#### Update Paper Work Deadline

**Endpoint**: `PATCH /admin_app/paperworks/<id>/deadline/`

**Permission**: IsAuthenticated, IsAdmin

**Request Body**:
```json
{
  "deadline": "datetime"
}
```

**Response**: PaperWork object

### Paper Management API

#### List Paper Works

**Endpoint**: `GET /api/paperworks/`

**Permission**: IsAuthenticated

**Notes**: 
- Researchers can only see their own paperworks
- Admins can see all paperworks

**Response**: Array of PaperWork objects

#### Get Paper Work Detail

**Endpoint**: `GET /api/paperworks/<id>/`

**Permission**: IsAuthenticated

**Notes**: 
- Researchers can only access their own paperworks
- Admins can access all paperworks

**Response**: PaperWork object

#### List Versions

**Endpoint**: `GET /api/paperworks/<id>/versions/`

**Permission**: IsAuthenticated

**Notes**: 
- Researchers can only access their own paperworks
- Admins can access all paperworks

**Response**: Array of Version objects

#### Submit Version

**Endpoint**: `POST /api/paperworks/<id>/versions/`

**Permission**: IsAuthenticated

**Notes**: 
- Only researchers can submit versions for their own paperworks

**Request Body**: Multipart form data
```
paper_pdf: file (required)
latex_tex: file (required)
python_zip: file (required)
docx_file: file (optional)
ai_percent_self: float (optional)
```

**Response**: Version object

#### Get Version Detail

**Endpoint**: `GET /api/paperworks/<id>/versions/<ver>/`

**Permission**: IsAuthenticated

**Notes**: 
- Researchers can only access their own paperworks
- Admins can access all paperworks

**Response**: 
```json
{
  "id": "uuid",
  "paperwork": { /* PaperWork object */ },
  "version_no": "integer",
  "submitted_at": "datetime",
  "pdf_path": "string",
  "latex_path": "string",
  "python_path": "string",
  "docx_path": "string",
  "ai_percent_self": "float",
  "ai_percent_verified": "float",
  "pdf_url": "string",
  "latex_url": "string",
  "python_url": "string"
}
```

#### Review Paper Work

**Endpoint**: `POST /api/paperworks/<id>/review/`

**Permission**: IsAuthenticated, IsAdmin

**Request Body**:
```json
{
  "status": "string", // One of: "ASSIGNED", "SUBMITTED", "CHANGES_REQUESTED", "APPROVED"
  "comments": "string" // Optional
}
```

**Response**: PaperWork object

#### Get All Paperwork Reviews

**Endpoint**: `GET /api/paperworks/<id>/reviews/`

**Permission**: IsAuthenticated

**Notes**: 
- Researchers can only access reviews for their own paperworks
- Admins can access all paperwork reviews

**Response**: Array of Review objects

#### Get Specific Paperwork Review

**Endpoint**: `GET /api/paperworks/<id>/reviews/<review_id>/`

**Permission**: IsAuthenticated

**Notes**: 
- Researchers can only access reviews for their own paperworks
- Admins can access all paperwork reviews

**Response**: Review object

#### Get Reports Summary

**Endpoint**: `GET /api/reports/summary/`

**Permission**: IsAuthenticated, IsAdmin

**Response**:
```json
{
  "total_papers": "integer",
  "papers_by_status": {
    "status1": "count",
    "status2": "count"
  },
  "papers_by_researcher": {
    "username1": "count",
    "username2": "count"
  },
  "average_ai_percentage": "float"
}
```

#### Export Reports

**Endpoint**: `GET /api/reports/export.csv/`

**Permission**: IsAuthenticated, IsAdmin

**Response**: CSV file with paper work data

#### Delete Paper Work

**Endpoint**: `DELETE /api/paperworks/<id>/delete/`

**Permission**: IsAuthenticated, IsNotFrozen, IsAdmin or PaperWork Owner

**Notes**: 
- Admins can delete any paperwork.
- Deletes associated files (PDF, LaTeX, Python, DOCX) from the file system.

**Response**: `204 No Content` on successful deletion.

#### Get Researcher Statistics

**Endpoint**: `GET /api/stats/researcher/`

**Permission**: IsAuthenticated, IsNotFrozen

**Notes**: 
- Researchers can only see their own statistics.

**Response**:
```json
{
  "total_paperworks": "integer",
  "pending_review": "integer",
  "approved": "integer",
  "changes_requested": "integer"
}
```

#### Get Admin Statistics

**Endpoint**: `GET /admin_app/stats/admin/`

**Permission**: IsAuthenticated, IsNotFrozen, IsAdmin

**Notes**: 
- Admins can see overall statistics.

**Response**:
```json
{
  "total_paperworks": "integer",
  "submitted": "integer",
  "approved": "integer",
  "changes_requested": "integer"
}
```

#### List Notifications

**Endpoint**: `GET /api/notifications/`

**Permission**: IsAuthenticated

**Notes**: 
- Researchers only see notifications for their papers
- Admins see all notifications

**Response**: Array of Notification objects

#### Mark Notification as Read

**Endpoint**: `POST /api/notifications/:id/`

**Permission**: IsAuthenticated

**Notes**: 
- Users can only mark their own notifications as read

**Request Body**:
```json
{
  "is_read": true
}
```

**Response**: Notification object

## Models

### User

```
id: UUID (primary key)
username: string
email: string
role: string (ADMIN, RESEARCHER)
status: string (ACTIVE, FROZEN, INACTIVE)
```

### PaperWork

```
id: UUID (primary key)
title: string
researcher: User (foreign key)
status: string (ASSIGNED, SUBMITTED, CHANGES_REQUESTED, APPROVED)
assigned_at: datetime
deadline: datetime (optional)
updated_at: datetime
```

### Version

```
id: UUID (primary key)
paperwork: PaperWork (foreign key)
version_no: integer
submitted_at: datetime
pdf_path: string
latex_path: string
python_path: string
docx_path: string (optional)
ai_percent_self: float
ai_percent_verified: float (optional)
```

### Notification

```
id: UUID (primary key)
event: string (WORK_ASSIGNED, SUBMITTED, CHANGES_REQUESTED, APPROVED)
paper: PaperWork (foreign key)
at: datetime
```

### Review

```
id: UUID (primary key)
paperwork: PaperWork (foreign key)
status: string (ASSIGNED, SUBMITTED, CHANGES_REQUESTED, APPROVED)
comments: string (optional)
created_at: datetime
updated_at: datetime
```

## Error Handling

The API returns standard HTTP status codes:

- 200: OK - Request succeeded
- 201: Created - Resource created successfully
- 400: Bad Request - Invalid input
- 401: Unauthorized - Authentication required
- 403: Forbidden - Permission denied
- 404: Not Found - Resource not found
- 500: Internal Server Error - Server error

Error responses include a JSON object with an error message:

```json
{
  "error": "Error message"
}
```

For validation errors, the response includes field-specific errors:

```json
{
  "field_name": [
    "Error message"
  ]
}
```