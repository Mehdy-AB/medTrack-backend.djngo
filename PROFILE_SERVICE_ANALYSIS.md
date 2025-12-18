# Profile Service Analysis & API Documentation

## Overview
The **Profile Service** is responsible for managing user profiles (Students, Encadrants) and organizational structures (Establishments, Services). It integrates with the Auth Service for user management and uses an event-driven architecture for data consistency.

## How to Add a User

There are two primary ways a user (profile) is created in the system:

### 1. Direct API Creation (Orchestrated)
You can create a user and their profile simultaneously by calling the Profile Service API. The service will:
1.  Create the user in the **Auth Service** (via internal API call).
2.  Create the profile in **Profile Service**.
3.  Publish a `CREATED` event.

**Endpoint for Student:**
-   **URL:** `POST /profile/api/students/`
-   **Body:**
    ```json
    {
        "email": "student@example.com",
        "password": "securepassword",
        "first_name": "John",
        "last_name": "Doe",
        "cin": "AB123456",
        "student_number": "S123456",
        "university": "MedTech",
        "program": "Software Engineering",
        "year_level": 3
    }
    ```

**Endpoint for Encadrant (Admin Only):**
-   **URL:** `POST /profile/api/encadrants/`
-   **Headers:** `Authorization: Bearer <admin_token>`
-   **Body:**
    ```json
    {
        "email": "supervisor@hospital.com",
        "password": "securepassword",
        "first_name": "Dr.",
        "last_name": "House",
        "cin": "CD987654",
        "establishment": "<establishment_uuid>",
        "service": "<service_uuid>",
        "position": "Head of Cardiology",
        "speciality": "Cardiology"
    }
    ```

### 2. Event-Driven (Reactive)
If a user is created directly in the **Auth Service**, the Profile Service listens for `auth.user.created` events and can automatically create a skeleton profile (depending on event handler implementation). *Note: The current explicit API implementation (`StudentViewSet.create`) is the recommended way to ensure full profile data is captured during registration.*

---

## API Endpoints

### Base URL
`/profile`

### Profiles

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| **GET** | `/profile/me` | Get current user's profile | Authenticated |

#### Students
**Base URL:** `/profile/api/students/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all students (Supports filtering: `?university=`, `?program=`, `?year_level=` and search: `?search=`) |
| `POST` | `/` | Create a new student (and Auth user) |
| `GET` | `/{id}/` | Get student details |
| `PUT` | `/{id}/` | Update student details |
| `PATCH`| `/{id}/` | Partial update student details |
| `DELETE`| `/{id}/` | Delete student |
| `GET` | `/by_user/{user_id}/` | Get student profile by Auth User ID |

#### Encadrants (Supervisors)
**Base URL:** `/profile/api/encadrants/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all encadrants (Supports search: `?search=` and filtering: `?speciality=`) |
| `POST` | `/` | Create a new encadrant (Admin only) |
| `GET` | `/{id}/` | Get encadrant details |
| `PUT` | `/{id}/` | Update encadrant details |
| `PATCH`| `/{id}/` | Partial update encadrant details |
| `DELETE`| `/{id}/` | Delete encadrant |
| `GET` | `/by_user/{user_id}/` | Get encadrant by Auth User ID |
| `GET` | `/by_establishment/{id}/` | List encadrants in an establishment |

### Organizations

#### Establishments (Hospitals)
**Base URL:** `/profile/api/establishments/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List establishments |
| `POST` | `/` | Create establishment (Admin/Encadrant) |
| `GET` | `/{id}/` | Get details |
| `PUT` | `/{id}/` | Update details |
| `DELETE`| `/{id}/` | Delete establishment |
| `GET` | `/by_city/{city}/` | Filter establishments by city |

#### Services (Departments)
**Base URL:** `/profile/api/services/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List services |
| `POST` | `/` | Create service (Admin/Encadrant) |
| `GET` | `/{id}/` | Get details |
| `PUT` | `/{id}/` | Update details |
| `DELETE`| `/{id}/` | Delete service |
| `GET` | `/by_establishment/{id}/` | List services in an establishment |

## Data Models

### Student
- Links to Auth User via `user_id`.
- Stores academic info (`university`, `program`, `student_number`).
- Contact info (`phone`, `cin`).

### Encadrant
- Links to Auth User via `user_id`.
- Linked to an `Establishment` and `Service`.
- Professional info (`position`, `speciality`).

### Establishment
- Represents a physical institution (e.g., Hospital).
- Fields: `name`, `city`, `address`, `type`.

### Service
- Represents a department within an Establishment.
- Fields: `name`, `capacity`, `description`.
