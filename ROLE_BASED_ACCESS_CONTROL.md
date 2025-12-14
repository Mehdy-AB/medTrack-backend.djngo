# Role-Based Access Control (RBAC) Documentation

## Overview

MedTrack implements role-based access control to restrict certain operations to specific user roles. The system uses JWT tokens to identify users and their roles, then enforces access restrictions at the endpoint level.

---

## User Roles

The system supports three roles:

| Role | Description | Permissions |
|------|-------------|-------------|
| `student` | Medical students doing internships | Read-only access to most resources |
| `encadrant` | Supervisors/mentors at hospitals | Can create/manage establishments, services, and users |
| `admin` | System administrators | Full access to all resources |

---

## How Role-Based Access Works

### 1. JWT Token Contains Role

When a user logs in or registers, they receive a JWT access token that includes their role:

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "encadrant",
  "type": "access",
  "iat": 1234567890,
  "exp": 1234568790,
  "iss": "auth-service"
}
```

### 2. JWT Middleware Extracts Role

The `JWTAuthMiddleware` automatically:
- Extracts the JWT token from `Authorization: Bearer <token>` header
- Validates and decodes the token
- Adds `user_data` to the request object with `user_id`, `email`, and `role`

**File:** `services/profile-service/src/profile_service/jwt_middleware.py`

```python
class JWTAuthMiddleware:
    def __call__(self, request):
        # Extract token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token = extract_token_from_header(auth_header)

        # Decode token and add to request
        request.user_data = decode_access_token(token)
        # user_data = {'user_id': '...', 'email': '...', 'role': 'encadrant'}
```

### 3. Endpoints Use `@require_role` Decorator

Endpoints that need role restrictions use the `@require_role()` decorator:

```python
from profile_service.jwt_middleware import require_role
from django.utils.decorators import method_decorator

class EstablishmentViewSet(viewsets.ModelViewSet):

    @method_decorator(require_role('encadrant'))
    def create(self, request, *args, **kwargs):
        """Only encadrants can create establishments"""
        return super().create(request, *args, **kwargs)
```

---

## Protected Endpoints

### PROFILE-SERVICE

#### Establishments (Hospitals)

| Endpoint | Method | Role Required | Description |
|----------|--------|---------------|-------------|
| `/profile/api/establishments/` | GET | None | List all establishments |
| `/profile/api/establishments/` | POST | `encadrant` | Create establishment |
| `/profile/api/establishments/{id}/` | GET | None | Get specific establishment |
| `/profile/api/establishments/{id}/` | PUT | `encadrant` | Update establishment |
| `/profile/api/establishments/{id}/` | PATCH | `encadrant` | Partial update |
| `/profile/api/establishments/{id}/` | DELETE | `encadrant` | Delete establishment |
| `/profile/api/establishments/by_city/{city}/` | GET | None | Filter by city |

#### Services (Hospital Departments)

| Endpoint | Method | Role Required | Description |
|----------|--------|---------------|-------------|
| `/profile/api/services/` | GET | None | List all services |
| `/profile/api/services/` | POST | `encadrant` | Create service |
| `/profile/api/services/{id}/` | GET | None | Get specific service |
| `/profile/api/services/{id}/` | PUT | `encadrant` | Update service |
| `/profile/api/services/{id}/` | PATCH | `encadrant` | Partial update |
| `/profile/api/services/{id}/` | DELETE | `encadrant` | Delete service |
| `/profile/api/services/by_establishment/{id}/` | GET | None | Filter by establishment |

#### Students

| Endpoint | Method | Role Required | Description |
|----------|--------|---------------|-------------|
| `/profile/api/students/` | GET | None | List all students |
| `/profile/api/students/` | POST | None | Create student profile |
| `/profile/api/students/{id}/` | GET | None | Get specific student |
| `/profile/api/students/{id}/` | PUT | None | Update student |
| `/profile/api/students/{id}/` | PATCH | None | Partial update |
| `/profile/api/students/{id}/` | DELETE | None | Delete student |
| `/profile/api/students/by_user/{user_id}/` | GET | None | Get by user_id |

#### Encadrants

| Endpoint | Method | Role Required | Description |
|----------|--------|---------------|-------------|
| `/profile/api/encadrants/` | GET | None | List all encadrants |
| `/profile/api/encadrants/` | POST | None | Create encadrant profile |
| `/profile/api/encadrants/{id}/` | GET | None | Get specific encadrant |
| `/profile/api/encadrants/{id}/` | PUT | None | Update encadrant |
| `/profile/api/encadrants/{id}/` | PATCH | None | Partial update |
| `/profile/api/encadrants/{id}/` | DELETE | None | Delete encadrant |
| `/profile/api/encadrants/by_user/{user_id}/` | GET | None | Get by user_id |
| `/profile/api/encadrants/by_establishment/{id}/` | GET | None | Filter by establishment |

---

### AUTH-SERVICE

#### User Management

| Endpoint | Method | Role Required | Description |
|----------|--------|---------------|-------------|
| `/auth/api/v1/register` | POST | None | Public registration |
| `/auth/api/v1/login` | POST | None | Public login |
| `/auth/api/v1/refresh` | POST | None | Refresh tokens |
| `/auth/api/v1/users/me` | GET | Authenticated | Get current user |
| `/auth/api/v1/users/me` | PATCH | Authenticated | Update profile |
| `/auth/api/v1/users/me/password` | PATCH | Authenticated | Change password |
| `/auth/api/v1/users` | GET | `admin` | List all users |
| `/auth/api/v1/users/{id}` | GET | `admin` | Get user details |
| `/auth/api/v1/users/{id}` | PATCH | `admin` | Update user |
| `/auth/api/v1/users/{id}` | DELETE | `admin` | Delete user |

---

## Testing Role-Based Access

### 1. Register as Encadrant

```bash
curl -X POST http://localhost/auth/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "encadrant@hospital.com",
    "password": "SecurePass123!",
    "first_name": "Dr. John",
    "last_name": "Smith",
    "role": "encadrant"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "user": {
    "id": "uuid",
    "email": "encadrant@hospital.com",
    "role": "encadrant"
  }
}
```

Save the `access_token` for subsequent requests.

---

### 2. Create Establishment (Encadrant Only)

#### ✅ With Encadrant Token (Success)

```bash
curl -X POST http://localhost/profile/api/establishments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <encadrant-access-token>" \
  -d '{
    "name": "City General Hospital",
    "city": "Casablanca",
    "address": "123 Main St",
    "type": "hospital"
  }'
```

**Response:** `201 Created`
```json
{
  "id": "establishment-uuid",
  "name": "City General Hospital",
  "city": "Casablanca",
  "address": "123 Main St",
  "type": "hospital"
}
```

#### ❌ Without Token (Fails)

```bash
curl -X POST http://localhost/profile/api/establishments/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "City General Hospital",
    "city": "Casablanca"
  }'
```

**Response:** `401 Unauthorized`
```json
{
  "error": "Authorization header required",
  "code": "NO_TOKEN"
}
```

#### ❌ With Student Token (Fails)

First, register as student:

```bash
curl -X POST http://localhost/auth/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePass123!",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "student"
  }'
```

Then try to create establishment with student token:

```bash
curl -X POST http://localhost/profile/api/establishments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <student-access-token>" \
  -d '{
    "name": "City General Hospital",
    "city": "Casablanca"
  }'
```

**Response:** `403 Forbidden`
```json
{
  "error": "Insufficient permissions",
  "code": "FORBIDDEN"
}
```

---

### 3. Create Service (Encadrant Only)

```bash
curl -X POST http://localhost/profile/api/services/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <encadrant-access-token>" \
  -d '{
    "name": "Cardiology Department",
    "establishment": "<establishment-uuid>",
    "type": "department"
  }'
```

**Response:** `201 Created` (only if authenticated as encadrant)

---

## Error Responses

### No Token Provided

**HTTP 401 Unauthorized**
```json
{
  "error": "Authorization header required",
  "code": "NO_TOKEN"
}
```

### Invalid or Expired Token

**HTTP 401 Unauthorized**
```json
{
  "error": "Token has expired",
  "code": "TOKEN_EXPIRED"
}
```

or

```json
{
  "error": "Invalid token",
  "code": "INVALID_TOKEN"
}
```

### Insufficient Permissions

**HTTP 403 Forbidden**
```json
{
  "error": "Insufficient permissions",
  "code": "FORBIDDEN"
}
```

---

## Implementation Details

### Adding Role Restrictions to New Endpoints

If you want to add role restrictions to a new endpoint:

**For ViewSet methods:**

```python
from django.utils.decorators import method_decorator
from profile_service.jwt_middleware import require_role

class MyViewSet(viewsets.ModelViewSet):

    @method_decorator(require_role('encadrant'))
    def create(self, request, *args, **kwargs):
        """Only encadrants can create"""
        return super().create(request, *args, **kwargs)

    @method_decorator(require_role('encadrant', 'admin'))
    def update(self, request, *args, **kwargs):
        """Encadrants or admins can update"""
        return super().update(request, *args, **kwargs)
```

**For function-based views:**

```python
from rest_framework.decorators import api_view
from profile_service.jwt_middleware import require_role

@api_view(['POST'])
@require_role('encadrant')
def my_endpoint(request):
    """Only encadrants can access"""
    return Response({'message': 'Success'})
```

**For multiple roles:**

```python
@require_role('encadrant', 'admin')
def my_endpoint(request):
    """Encadrants or admins can access"""
    return Response({'message': 'Success'})
```

---

### Getting Current User Information

Within a protected endpoint, you can access user information:

```python
def my_endpoint(request):
    # Get user data from JWT
    user_data = getattr(request, 'user_data', {})

    user_id = user_data.get('user_id')     # UUID string
    email = user_data.get('email')         # user@example.com
    role = user_data.get('role')           # 'student', 'encadrant', or 'admin'

    # Use this information
    if role == 'encadrant':
        # Special logic for encadrants
        pass
```

Or use helper functions:

```python
from profile_service.jwt_middleware import get_current_user_id, get_current_user_role

def my_endpoint(request):
    user_id = get_current_user_id(request)
    role = get_current_user_role(request)
```

---

## Security Best Practices

### ✅ DO:
- **Always use HTTPS in production** - JWT tokens should never be sent over unencrypted connections
- **Set short expiration times** - Access tokens expire in 15 minutes (900 seconds)
- **Use refresh tokens** - For long-lived sessions, use refresh tokens to get new access tokens
- **Validate tokens on every request** - The middleware does this automatically
- **Check specific roles** - Use `@require_role('encadrant')` instead of just checking authentication
- **Log access attempts** - Track who is accessing protected resources

### ❌ DON'T:
- **Don't store JWT tokens in localStorage** - Use httpOnly cookies or sessionStorage
- **Don't send tokens in URL parameters** - Always use Authorization header
- **Don't trust client-side role checks** - Always enforce roles on the server
- **Don't skip role validation** - Even for "internal" endpoints
- **Don't log JWT tokens** - They contain sensitive information

---

## Troubleshooting

### Problem: Always getting "Authorization header required"

**Cause:** Missing or incorrectly formatted Authorization header

**Solution:** Ensure header format is exactly:
```
Authorization: Bearer <token>
```

NOT:
- `Authorization: <token>` (missing "Bearer")
- `Authorization: bearer <token>` (lowercase "bearer")
- `Token: <token>` (wrong header name)

---

### Problem: "Insufficient permissions" even with correct role

**Cause:** Token might be stale or role changed after token was issued

**Solution:**
1. Login again to get fresh token
2. Check token contents by decoding it at https://jwt.io
3. Verify the `role` claim matches expected role

---

### Problem: Token expired immediately after login

**Cause:** System clock mismatch or token lifetime too short

**Solution:**
1. Check server system time: `docker exec auth-service date`
2. Verify JWT settings in AUTH-SERVICE settings.py
3. Check token expiration time in JWT payload

---

## Summary

Role-based access control in MedTrack:

1. ✅ **JWT-based authentication** - Roles embedded in access tokens
2. ✅ **Middleware validation** - Automatic token validation on every request
3. ✅ **Decorator-based authorization** - Simple `@require_role()` decorator
4. ✅ **Granular permissions** - Different roles for different operations
5. ✅ **Clear error messages** - Detailed error codes for troubleshooting

**Current Role Restrictions:**
- **Establishments (Hospitals)**: Create/Update/Delete → `encadrant` only
- **Services (Departments)**: Create/Update/Delete → `encadrant` only
- **User Management**: Admin operations → `admin` only
- **Registration**: Public (anyone can register)

**Future Enhancements:**
- Add `admin` role checks to more endpoints
- Implement resource-based permissions (users can only modify their own data)
- Add audit logging for all protected operations
- Implement role hierarchy (admin inherits encadrant permissions)

---

## Implementation Notes (2025-12-13)

### JWT Secret Key Configuration

All services must use the same `JWT_SECRET_KEY` environment variable for JWT token validation to work across services. This has been configured in `docker-compose.yml`:

```yaml
environment:
  - JWT_SECRET_KEY=shared-jwt-secret-key-change-in-production-12345
```

Applied to all services:
- auth-service
- profile-service
- profile-service-consumer
- core-service
- eval-service
- comm-service
- comm-service-consumer

### ViewSet Method Decorator Fix

The `@require_role` decorator was updated to work properly with Django REST Framework ViewSet methods. The decorator now:

1. Uses `@functools.wraps` to preserve function metadata
2. Handles both function-based views and ViewSet methods
3. Correctly extracts the `request` parameter from ViewSet method calls

**File:** `services/profile-service/src/profile_service/jwt_middleware.py`

```python
def require_role(*allowed_roles):
    from functools import wraps

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self_or_request, *args, **kwargs):
            # Handle both function-based views and ViewSet methods
            if hasattr(self_or_request, 'user_data'):
                # Function-based view: first arg is request
                request = self_or_request
            else:
                # ViewSet method: first arg is self, second is request
                request = args[0] if args else kwargs.get('request')

            user_data = getattr(request, 'user_data', None)
            if not user_data:
                return JsonResponse(
                    {'error': 'Authentication required', 'code': 'AUTH_REQUIRED'},
                    status=401
                )

            if user_data.get('role') not in allowed_roles:
                return JsonResponse(
                    {'error': 'Insufficient permissions', 'code': 'FORBIDDEN'},
                    status=403
                )

            return view_func(self_or_request, *args, **kwargs)
        return wrapper
    return decorator
```

### ViewSet Decorator Usage

Applied `@require_role('encadrant')` directly (without `@method_decorator`) to protected ViewSet methods:

**File:** `services/profile-service/src/profiles/views.py`

```python
class EstablishmentViewSet(viewsets.ModelViewSet):
    @require_role('encadrant')
    def create(self, request, *args, **kwargs):
        # ...

    @require_role('encadrant')
    def update(self, request, *args, **kwargs):
        # ...

    @require_role('encadrant')
    def partial_update(self, request, *args, **kwargs):
        # ...

    @require_role('encadrant')
    def destroy(self, request, *args, **kwargs):
        # ...
```

### Verification Tests

All role-based access control tests passed successfully:

| Test | Role | Endpoint | Expected | Result |
|------|------|----------|----------|--------|
| Create Hospital | student | POST /profile/api/establishments/ | 403 Forbidden | ✅ Pass |
| Create Hospital | encadrant | POST /profile/api/establishments/ | 201 Created | ✅ Pass |
| Create Service | student | POST /profile/api/services/ | 403 Forbidden | ✅ Pass |
| Create Service | encadrant | POST /profile/api/services/ | 201 Created | ✅ Pass |

### Test Users

**Encadrant:**
- Email: `dr.encadrant@example.com`
- Password: `StrongPassword123!`
- Role: `encadrant`

**Student:**
- Email: `student.test@example.com`
- Password: `StudentPass123`
- Role: `student`
