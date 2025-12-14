# Auth Service API & Events Documentation

## Base URL
`http://localhost/auth/api/v1`

## API Endpoints

### Authentication

#### 1. Register User
**POST** `/register`

Public endpoint to create a new user account.

**Request:**
```json
{
  "email": "student@example.com",
  "password": "StrongPassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "role": "student"  // Optional, defaults to 'student'
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "refresh_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": "a1b2c3d4-...",
    "email": "student@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "role": "student",
    "is_active": true,
    "created_at": "2025-12-12T16:00:00Z",
    "updated_at": "2025-12-12T16:00:00Z"
  }
}
```

#### 2. Login
**POST** `/login`

Authenticate user with credentials.

**Request:**
```json
{
  "email": "student@example.com",
  "password": "StrongPassword123!"
}
```

**Response (200 OK):**
Same structure as Register response.

#### 3. Refresh Token
**POST** `/refresh`

Get a new access token using a valid refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1Ni..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

### User Management

#### 4. Get Current User Profile
**GET** `/users/me`
**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "id": "a1b2c3d4-...",
  "email": "student@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "role": "student",
  "is_active": true,
  "created_at": "...",
  "updated_at": "..."
}
```

#### 5. Update Profile
**PATCH** `/users/me`
**Headers:** `Authorization: Bearer <access_token>`

**Request:** (All fields optional)
```json
{
  "first_name": "Johnny",
  "phone": "+0987654321"
}
```

**Response (200 OK):** Updated user object.

#### 6. Change Password
**PATCH** `/users/me/password`
**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "old_password": "StrongPassword123!",
  "new_password": "NewStrongPassword456!"
}
```

**Response (200 OK):** New tokens (old sessions revoked).

### Session Management

#### 7. List Active Sessions
**GET** `/sessions`
**Headers:** `Authorization: Bearer <access_token>`

#### 8. Revoke Session
**DELETE** `/sessions/{session_id}`
**Headers:** `Authorization: Bearer <access_token>`

### Audit Logs (Admin Only)

#### 9. List Audit Logs
**GET** `/audit-logs`
**Headers:** `Authorization: Bearer <access_token>`
**Query Params:** `user_id`, `action`, `entity`

---

## RabbitMQ Events

**Exchange:** `events.topic`
**Topic Type:** `topic`

### 1. User Created
**Routing Key:** `auth.user.created`

Published when a new user registers.

```json
{
  "event_type": "USER_CREATED",
  "user_id": "a1b2c3d4-...",
  "email": "student@example.com",
  "role": "student",
  "first_name": "John",
  "last_name": "Doe",
  "_meta": {
    "timestamp": "2025-12-12T16:00:00Z",
    "routing_key": "auth.user.created",
    "source": "auth-service"
  }
}
```

### 2. User Updated
**Routing Key:** `auth.user.updated`

Published when a user updates their profile.

```json
{
  "event_type": "USER_UPDATED",
  "user_id": "a1b2c3d4-...",
  "email": "student@example.com",
  "changed_fields": ["first_name", "phone"],
  "_meta": { ... }
}
```

### 3. User Role Changed
**Routing Key:** `auth.user.role_changed`

Published when an admin changes a user's role.

```json
{
  "event_type": "USER_ROLE_CHANGED",
  "user_id": "a1b2c3d4-...",
  "email": "student@example.com",
  "old_role": "student",
  "new_role": "encadrant",
  "_meta": { ... }
}
```

### 4. Password Changed
**Routing Key:** `auth.password.changed`

Published when a user changes their password.

```json
{
  "event_type": "PASSWORD_CHANGED",
  "user_id": "a1b2c3d4-...",
  "email": "student@example.com",
  "_meta": { ... }
}
```

### 5. Session Revoked
**Routing Key:** `auth.session.revoked`

Published when a session is manually revoked or during password change.

```json
{
  "event_type": "SESSION_REVOKED",
  "session_id": "s1s2s3s4-...",
  "user_id": "a1b2c3d4-...",
  "_meta": { ... }
}
```

### 6. User Deleted
**Routing Key:** `auth.user.deleted`

Published when an admin deletes a user.

```json
{
  "event_type": "USER_DELETED",
  "user_id": "a1b2c3d4-...",
  "email": "student@example.com",
  "_meta": { ... }
}
```
