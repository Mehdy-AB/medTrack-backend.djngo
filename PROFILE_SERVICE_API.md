# PROFILE SERVICE - API Documentation

## Overview
The Profile Service manages hospitals (establishments), departments (services), students, and supervisors (encadrants).

**Base URL:** `http://localhost/profile/api/`

---

## 📊 Database Schema

### Tables Created:
- ✅ **establishments** - Hospitals/medical facilities
- ✅ **services** - Departments/units within hospitals
- ✅ **students** - Student profiles (references AUTH-SERVICE user_id)
- ✅ **encadrants** - Supervisor/mentor profiles (references AUTH-SERVICE user_id)

---

## 🏥 ESTABLISHMENTS (Hospitals)

### List All Establishments
```bash
GET http://localhost/profile/api/establishments/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Hospital Central",
    "type": "Public Hospital",
    "address": "123 Main Street",
    "city": "Casablanca",
    "phone": "+212-555-1234",
    "metadata": {"capacity": 500, "emergency": true},
    "created_at": "2025-12-11T17:00:00Z",
    "updated_at": "2025-12-11T17:00:00Z"
  }
]
```

### Create Establishment
```bash
POST http://localhost/profile/api/establishments/
Content-Type: application/json

{
  "name": "Hospital Central",
  "type": "Public Hospital",
  "address": "123 Main Street",
  "city": "Casablanca",
  "phone": "+212-555-1234",
  "metadata": {"capacity": 500, "emergency": true}
}
```

### Get Establishment by ID
```bash
GET http://localhost/profile/api/establishments/{id}/
```

### Update Establishment
```bash
PUT http://localhost/profile/api/establishments/{id}/
# or
PATCH http://localhost/profile/api/establishments/{id}/

{
  "phone": "+212-555-9999"
}
```

### Delete Establishment
```bash
DELETE http://localhost/profile/api/establishments/{id}/
```

### Filter by City
```bash
GET http://localhost/profile/api/establishments/by_city/Casablanca/
```

---

## 🏬 SERVICES (Hospital Departments)

### List All Services
```bash
GET http://localhost/profile/api/services/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "establishment": "establishment-uuid",
    "establishment_name": "Hospital Central",
    "name": "Cardiology",
    "description": "Heart and cardiovascular care",
    "capacity": 50,
    "metadata": {"equipment": ["ECG", "MRI"]},
    "created_at": "2025-12-11T17:00:00Z",
    "updated_at": "2025-12-11T17:00:00Z"
  }
]
```

### Create Service
```bash
POST http://localhost/profile/api/services/
Content-Type: application/json

{
  "establishment": "establishment-uuid",
  "name": "Cardiology",
  "description": "Heart and cardiovascular care",
  "capacity": 50,
  "metadata": {"equipment": ["ECG", "MRI"]}
}
```

### Get Service by ID
```bash
GET http://localhost/profile/api/services/{id}/
```

### Update Service
```bash
PATCH http://localhost/profile/api/services/{id}/

{
  "capacity": 60
}
```

### Delete Service
```bash
DELETE http://localhost/profile/api/services/{id}/
```

### Filter by Establishment
```bash
GET http://localhost/profile/api/services/by_establishment/{establishment_id}/
```

---

## 🎓 STUDENTS

### List All Students
```bash
GET http://localhost/profile/api/students/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "user_id": "11111111-1111-1111-1111-111111111111",
    "student_number": "STU001",
    "date_of_birth": "2000-01-15",
    "university": "Mohammed V University",
    "program": "Medicine",
    "year_level": 3,
    "extra": {"specialization": "Cardiology"},
    "user_data": {
      "id": "11111111-1111-1111-1111-111111111111",
      "email": "john.doe@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+1234567890",
      "role": "student",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    "created_at": "2025-12-11T17:00:00Z",
    "updated_at": "2025-12-11T17:00:00Z"
  }
]
```

**Note:** `user_data` is fetched from AUTH-SERVICE (currently returns mock data)

### Create Student
```bash
POST http://localhost/profile/api/students/
Content-Type: application/json

{
  "user_id": "11111111-1111-1111-1111-111111111111",
  "student_number": "STU001",
  "date_of_birth": "2000-01-15",
  "university": "Mohammed V University",
  "program": "Medicine",
  "year_level": 3,
  "extra": {"specialization": "Cardiology"}
}
```

### Get Student by ID
```bash
GET http://localhost/profile/api/students/{id}/
```

### Get Student by User ID (with AUTH-SERVICE data)
```bash
GET http://localhost/profile/api/students/by_user/{user_id}/
```

This endpoint automatically fetches and includes user data from AUTH-SERVICE!

### Update Student
```bash
PATCH http://localhost/profile/api/students/{id}/

{
  "year_level": 4,
  "extra": {"specialization": "Surgery"}
}
```

### Delete Student
```bash
DELETE http://localhost/profile/api/students/{id}/
```

---

## 👨‍⚕️ ENCADRANTS (Supervisors/Mentors)

### List All Encadrants
```bash
GET http://localhost/profile/api/encadrants/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "user_id": "22222222-2222-2222-2222-222222222222",
    "establishment": "establishment-uuid",
    "establishment_name": "Hospital Central",
    "service": "service-uuid",
    "service_name": "Cardiology",
    "position": "Senior Consultant",
    "specialty": "Cardiology",
    "contact": {"office": "Room 305", "extension": "1234"},
    "user_data": {
      "id": "22222222-2222-2222-2222-222222222222",
      "email": "dr.smith@example.com",
      "first_name": "Alice",
      "last_name": "Smith",
      "phone": "+1111111111",
      "role": "encadrant",
      "is_active": true
    },
    "created_at": "2025-12-11T17:00:00Z",
    "updated_at": "2025-12-11T17:00:00Z"
  }
]
```

### Create Encadrant
```bash
POST http://localhost/profile/api/encadrants/
Content-Type: application/json

{
  "user_id": "22222222-2222-2222-2222-222222222222",
  "establishment": "establishment-uuid",
  "service": "service-uuid",
  "position": "Senior Consultant",
  "specialty": "Cardiology",
  "contact": {"office": "Room 305", "extension": "1234"}
}
```

### Get Encadrant by ID
```bash
GET http://localhost/profile/api/encadrants/{id}/
```

### Get Encadrant by User ID (with AUTH-SERVICE data)
```bash
GET http://localhost/profile/api/encadrants/by_user/{user_id}/
```

### Filter by Establishment
```bash
GET http://localhost/profile/api/encadrants/by_establishment/{establishment_id}/
```

### Update Encadrant
```bash
PATCH http://localhost/profile/api/encadrants/{id}/

{
  "position": "Head of Department",
  "contact": {"office": "Room 401"}
}
```

### Delete Encadrant
```bash
DELETE http://localhost/profile/api/encadrants/{id}/
```

---

## 🔗 Integration with Other Microservices

### Service Clients Available

The Profile Service can call other microservices using the service client layer in `service_client.py`.

All service clients are configured with **mock data** that you can easily replace with real HTTP calls later.

### 1. AUTH-SERVICE Client

**Methods:**
- `AuthServiceClient.get_user_by_id(user_id)` - Get user details
- `AuthServiceClient.get_users_by_role(role)` - Get all users with a role
- `AuthServiceClient.verify_user_exists(user_id)` - Check if user exists

**Currently:** Returns mock user data
**Real Endpoint:** `GET http://auth-service:8000/auth/api/users/{user_id}/`

### 2. PROFILE-SERVICE Client (Self-Reference)

**Methods:**
- `ProfileServiceClient.get_student_by_id(student_id)` - Get student details
- `ProfileServiceClient.get_student_by_user_id(user_id)` - Get student by user_id
- `ProfileServiceClient.get_encadrant_by_id(encadrant_id)` - Get encadrant details
- `ProfileServiceClient.get_establishment_by_id(establishment_id)` - Get hospital details

**Currently:** Returns mock data
**Real Endpoints:**
- `GET http://profile-service:8000/profile/api/students/{id}/`
- `GET http://profile-service:8000/profile/api/students/by_user/{user_id}/`
- `GET http://profile-service:8000/profile/api/encadrants/{id}/`
- `GET http://profile-service:8000/profile/api/establishments/{id}/`

### 3. CORE-SERVICE Client

**Methods:**
- `CoreServiceClient.get_offer_by_id(offer_id)` - Get internship offer details
- `CoreServiceClient.get_stage_by_id(stage_id)` - Get stage/assignment details

**Currently:** Returns mock data
**Real Endpoints (when CORE-SERVICE is ready):**
- `GET http://core-service:8000/core/api/offers/{id}/`
- `GET http://core-service:8000/core/api/stages/{id}/`

### 4. COMM-SERVICE Client

**Methods:**
- `CommServiceClient.send_notification(user_id, title, content, type)` - Send notification

**Currently:** Returns True (mock)
**Real Endpoint (when COMM-SERVICE is ready):**
- `POST http://comm-service:8000/comm/api/notifications/`

---

### How Student/Encadrant Endpoints Include User Data

When you call:
```bash
GET /profile/api/students/by_user/{user_id}/
GET /profile/api/encadrants/by_user/{user_id}/
```

The response automatically includes `user_data` from AUTH-SERVICE:

**Example Response:**
```json
{
  "id": "uuid",
  "user_id": "11111111-1111-1111-1111-111111111111",
  "student_number": "STU001",
  "user_data": {
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }
}
```

---

### To Enable Real Service Calls

When your friends' services are ready:

**File:** `services/profile-service/src/profiles/service_client.py`

For each client method:
1. Find the method (e.g., `get_user_by_id()`)
2. Uncomment the actual HTTP call code (marked with `# TODO:`)
3. Comment out the mock return statement
4. Rebuild: `docker-compose up -d --build profile-service`

**Example:**
```python
# Before (Mock):
return {"id": user_id, "email": "mock@example.com"}

# After (Real):
response = requests.get(f"{AUTH_SERVICE_URL}/auth/api/users/{user_id}/", timeout=5)
return response.json() if response.status_code == 200 else None
```

---

## 📝 Complete Example Workflow

### 1. Create a Hospital
```bash
curl -X POST 'http://localhost/profile/api/establishments/' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Hospital Central",
    "type": "Public Hospital",
    "city": "Casablanca",
    "phone": "+212-555-1234"
  }'
```

**Response:**
```json
{
  "id": "a1b2c3d4-...",
  "name": "Hospital Central",
  ...
}
```

### 2. Create a Department
```bash
curl -X POST 'http://localhost/profile/api/services/' \
  -H 'Content-Type: application/json' \
  -d '{
    "establishment": "a1b2c3d4-...",
    "name": "Cardiology",
    "capacity": 50
  }'
```

### 3. Create a Student
```bash
curl -X POST 'http://localhost/profile/api/students/' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "11111111-1111-1111-1111-111111111111",
    "student_number": "STU001",
    "university": "Mohammed V University",
    "program": "Medicine",
    "year_level": 3
  }'
```

### 4. Get Student with User Data
```bash
curl 'http://localhost/profile/api/students/by_user/11111111-1111-1111-1111-111111111111/'
```

**Response includes user data from AUTH-SERVICE:**
```json
{
  "id": "...",
  "user_id": "11111111-1111-1111-1111-111111111111",
  "student_number": "STU001",
  "university": "Mohammed V University",
  "program": "Medicine",
  "year_level": 3,
  "user_data": {
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }
}
```

### 5. Create an Encadrant
```bash
curl -X POST 'http://localhost/profile/api/encadrants/' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "22222222-2222-2222-2222-222222222222",
    "establishment": "a1b2c3d4-...",
    "service": "b2c3d4e5-...",
    "position": "Senior Consultant",
    "specialty": "Cardiology"
  }'
```

---

## 🛠️ Testing Tips

### Using curl:
```bash
# List all
curl http://localhost/profile/api/students/

# Create
curl -X POST http://localhost/profile/api/students/ \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"...","student_number":"STU001"}'

# Update
curl -X PATCH http://localhost/profile/api/students/{id}/ \
  -H 'Content-Type: application/json' \
  -d '{"year_level": 4}'

# Delete
curl -X DELETE http://localhost/profile/api/students/{id}/
```

### Using Postman/Insomnia:
Import these endpoints and test with a GUI tool.

---

## ✅ Summary

Your PROFILE-SERVICE is fully functional with:

- ✅ All 4 tables created (establishments, services, students, encadrants)
- ✅ UUID primary keys
- ✅ JSONB metadata/extra/contact fields
- ✅ Proper indexes on foreign keys and user_id
- ✅ Full CRUD operations
- ✅ Custom filter endpoints
- ✅ **Mock integration with AUTH-SERVICE** (ready to switch to real calls)
- ✅ RESTful API with Django REST Framework
- ✅ Automatic timestamp tracking (created_at, updated_at)

**Next Steps:**
1. Test all endpoints with curl or Postman
2. When AUTH-SERVICE is ready, update `service_client.py` to use real HTTP calls
3. Coordinate with your friend on the AUTH-SERVICE API contract
