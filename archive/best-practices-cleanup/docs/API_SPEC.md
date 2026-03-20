# API Specification Template

Use this file as the living API specification for your project.
Replace all `<placeholder>` values with your project's actual endpoint names,
fields, and business rules. Keep this document in sync with your controllers.

Base URL: `/api/v1`
Auth: `Authorization: Bearer <accessToken>` or `Cookie: accessToken=<token>`
Content-Type: `application/json`

---

## Standard Response Envelope

All endpoints return one of these three shapes — no exceptions.

### Success
```json
{ "success": true, "message": "Optional message", "data": { } }
```

### Paginated
```json
{
  "success": true,
  "data": [ ],
  "meta": { "total": 100, "page": 1, "limit": 20, "lastPage": 5 }
}
```

### Error
```json
{
  "success": false,
  "message": "Human-readable error",
  "data": null,
  "errors": [ { "field": "email", "message": "must be a valid email" } ]
}
```

---

## Authentication — `/auth`

### User Authentication (all user roles)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/<role>/signup` | Public | Register new user |
| POST | `/auth/<role>/login` | Public | Authenticate, receive tokens |
| POST | `/auth/<role>/logout` | JWT | Invalidate session |
| POST | `/auth/<role>/refresh-token` | Refresh JWT | Obtain new access token |
| POST | `/auth/<role>/verify-email` | Public | Verify email address with OTP |
| POST | `/auth/<role>/resend-verification` | Public | Re-send verification email |
| POST | `/auth/<role>/forgot-password` | Public | Request password reset link |
| POST | `/auth/<role>/reset-password` | Public | Submit new password via reset token |
| PATCH | `/auth/<role>/change-password` | JWT | Change password while authenticated |
| GET | `/auth/<role>/profile` | JWT | Retrieve own user profile |
| PATCH | `/auth/<role>/profile` | JWT | Update own profile fields |
| PATCH | `/auth/<role>/preferences` | JWT | Update UI preferences (theme, language, etc.) |

### Admin Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/admin/login` | Public | Admin login |
| POST | `/auth/admin/logout` | JWT | Admin logout |

### OAuth (optional)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/auth/google` | Public | Initiate Google OAuth flow |
| GET | `/auth/google/callback` | Public | OAuth callback — issues tokens |

---

## Example: Signup Request/Response

### POST `/auth/<role>/signup`

**Request:**
```json
{
  "firstName": "Jane",
  "lastName": "Smith",
  "email": "jane@example.com",
  "password": "SecurePass123!",
  "mobileNumber": "+1234567890"
}
```
> Add or remove fields according to your project's registration requirements.

**Response 201:**
```json
{
  "success": true,
  "message": "Registration successful. Please verify your email.",
  "data": {
    "user": {
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "firstName": "Jane",
      "lastName": "Smith",
      "email": "jane@example.com",
      "isEmailVerified": false,
      "userType": 2
    },
    "accessToken": "<jwt>",
    "refreshToken": "<jwt>"
  }
}
```

**Response 400 (Validation Error):**
```json
{
  "success": false,
  "message": "Validation failed",
  "data": null,
  "errors": [
    { "field": "email", "message": "email must be a valid email" },
    { "field": "password", "message": "password is too weak" }
  ]
}
```

---

## Example: Login Request/Response

### POST `/auth/<role>/login`

**Request:**
```json
{ "email": "jane@example.com", "password": "SecurePass123!" }
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "user": { "uuid": "...", "firstName": "Jane", "email": "jane@example.com" },
    "accessToken": "<jwt>",
    "refreshToken": "<jwt>"
  }
}
```

**Response 401:**
```json
{ "success": false, "message": "Invalid credentials", "data": null }
```

---

## Example: Profile Response

### GET `/auth/<role>/profile`

**Response 200:**
```json
{
  "success": true,
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "firstName": "Jane",
    "lastName": "Smith",
    "email": "jane@example.com",
    "isEmailVerified": true,
    "userType": 2,
    "status": 1,
    "theme": "light",
    "language": "en",
    "createdAt": "2024-01-01T00:00:00.000Z"
  }
}
```
> Add project-specific profile fields here (e.g., domain-specific metadata flattened from `meta` JSONB).

---

## Domain Resources

Document your project's domain-specific API groups here.
Each group follows the standard REST pattern below.

### Template: Resource CRUD

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/<resources>` | JWT | List resources (paginated) |
| POST | `/<resources>` | JWT | Create resource |
| GET | `/<resources>/:uuid` | JWT | Get single resource |
| PATCH | `/<resources>/:uuid` | JWT | Update resource |
| DELETE | `/<resources>/:uuid` | JWT | Delete resource |
| GET | `/<resources>/:uuid/<sub-resources>` | JWT | List nested sub-resources |

### Template: Resource Action (non-CRUD)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/<resources>/:uuid/<action>` | JWT | Trigger an action on resource |

---

## File Management — `/files`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/files/upload` | JWT | Upload a file (multipart/form-data) |
| GET | `/files/:uuid` | JWT | Get file metadata |
| GET | `/files/:uuid/download` | JWT | Get signed download URL |
| DELETE | `/files/:uuid` | JWT | Delete file |

**Upload Response 201:**
```json
{
  "success": true,
  "data": {
    "uuid": "...",
    "originalName": "report.pdf",
    "mimeType": "application/pdf",
    "size": 204800,
    "url": "https://cdn.example.com/signed-url"
  }
}
```

---

## Common Query Parameters

### Pagination
```
?page=1&limit=20
```
Default: `page=1`, `limit=20`. Maximum `limit` is 100.

### Filtering
```
?status=1&<field>=<value>
```

### Sorting
```
?sortBy=createdAt&sortOrder=desc
```
`sortOrder` accepts `asc` or `desc`.

### Relation Includes
```
?include=roles,company
```
Comma-separated list of relations to eager-load in the response.

### Search
```
?search=<term>
```

---

## Standard HTTP Status Codes

| Code | When to Use |
|------|------------|
| 200 | Successful GET, PATCH, DELETE |
| 201 | Successful POST creating a resource |
| 400 | Validation errors, malformed request |
| 401 | Missing, expired, or invalid token |
| 403 | Authenticated but not authorized for this action |
| 404 | Resource does not exist |
| 409 | Conflict — e.g., duplicate unique field |
| 422 | Semantic validation error |
| 429 | Rate limit exceeded |
| 500 | Unexpected server error |

---

## Swagger UI

Available in non-production environments at:
```
http://localhost:<PORT>/api/docs
```

Disabled when `NODE_ENV=production`.

All controllers must use `@ApiTags()`, all endpoints `@ApiOperation()` + `@ApiResponse()`,
all DTO fields `@ApiProperty()`.
