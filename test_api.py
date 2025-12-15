#!/usr/bin/env python3
"""
MedTrack API Integration Test Suite
====================================
Tests all major API endpoints across microservices.

Usage:
    1. Start the stack: docker-compose up -d
    2. Wait for services to be healthy
    3. Run: python test_api.py

Environment Variables (optional):
    BASE_URL: Base URL for the API gateway (default: http://localhost)
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Configuration
BASE_URL = "http://localhost"
AUTH_URL = f"{BASE_URL}/auth/api/v1"
PROFILE_URL = f"{BASE_URL}/profile"

# Test data storage
test_data = {
    "admin_token": None,
    "student_token": None,
    "encadrant_token": None,
    "admin_user": None,
    "student_user": None,
    "encadrant_user": None,
    "establishment_id": None,
    "service_id": None,
    "student_profile_id": None,
    "encadrant_profile_id": None,
    "offer_id": None,
    "message_id": None,
    "notification_id": None,
}


def log_test(name: str, passed: bool, details: str = ""):
    """Log test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if details and not passed:
        print(f"       Details: {details}")


def api_call(
    method: str,
    endpoint: str,
    token: Optional[str] = None,
    data: Optional[Dict] = None,
    expected_status: int = 200
) -> Optional[Dict]:
    """Make an API call and return the response."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return None

        if response.status_code == expected_status:
            if response.content:
                return response.json()
            return {}
        else:
            print(f"       Unexpected status: {response.status_code} (expected {expected_status})")
            if response.content:
                try:
                    print(f"       Response: {response.json()}")
                except:
                    print(f"       Response: {response.text[:200]}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"       Request failed: {e}")
        return None


# ============================================
# AUTH SERVICE TESTS
# ============================================

def test_health_checks():
    """Test health endpoints for all services."""
    print("\n" + "="*60)
    print("HEALTH CHECKS")
    print("="*60)

    services = [
        ("/auth/health", "Auth Service"),
        ("/profile/health", "Profile Service"),
        ("/core/health", "Core Service"),
        ("/comm/health", "Comm Service"),
        ("/eval/health", "Eval Service"),
    ]

    for endpoint, name in services:
        result = api_call("GET", endpoint, token=test_data["admin_token"])
        log_test(f"{name} Health", result is not None)



# ============================================
# AUTH SERVICE - BOOTSTRAP ADMIN
# ============================================

def create_initial_admin():
    """Create initial admin user via Docker exec."""
    print("Bootstrap Admin User...")
    
    email = "admin@medtrack.com"
    password = "password123"
    
    # Check if admin already exists via API
    login_data = {
        "email": email,
        "password": password
    }
    try:
        response = requests.post(f"{AUTH_URL}/login", json=login_data)
        if response.status_code == 200:
            print(f"✅ Admin already exists.")
            test_data['admin_email'] = email
            test_data['admin_password'] = password
            test_data['admin_token'] = response.json()['access_token']
            test_data['admin_user'] = response.json()['user']
            return
    except:
        pass

    # Create via Docker
    print(f"Creating admin user via Docker exec...")
    cmd = [
        "docker", "exec", "auth-service", "python", "manage.py", "shell", "-c",
        f"from users.models import User; u, _ = User.objects.get_or_create(email='{email}', defaults={{'role': 'admin', 'is_active': True, 'first_name': 'Admin'}}); u.set_password('{password}'); u.role='admin'; u.save()"
    ]
    
    try:
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to create admin: {result.stderr}")
            return
        
        print(f"✅ Admin user created/verified via Docker.")
        test_data['admin_email'] = email
        test_data['admin_password'] = password
        
    except Exception as e:
        print(f"❌ Error bootstrapping admin: {e}")

def test_bootstrap_admin():
    create_initial_admin()




# ============================================
# AUTH SERVICE - LOGIN (Existing Users)
# ============================================

def test_admin_login():
    """Test admin login."""
    pass # Header

    data = {
        "email": test_data.get('admin_email', 'admin@medtrack.com'),
        "password": test_data.get('admin_password', 'password123')
    }
    response = requests.post(f"{AUTH_URL}/login", json=data)
    
    if response.status_code == 200:
        print(f"✅ PASS | Admin Login Successful")
        test_data['admin_token'] = response.json()['access_token']
        test_data['admin_user'] = response.json()['user']
    else:
        print(f"❌ FAIL | Status: {response.status_code}, Response: {response.text}")


def test_student_login():
    """Test student login (verify Auth creation)."""
    if 'student_email' not in test_data:
        print("⚠️ Skipping Student Login (No student created)")
        return

    data = {
        "email": test_data['student_email'],
        "password": test_data['student_password']
    }
    response = requests.post(f"{AUTH_URL}/login", json=data)
    
    if response.status_code == 200:
        print(f"✅ PASS | Student Login Successful")
        test_data['student_token'] = response.json()['access_token']
    else:
        print(f"❌ FAIL | Status: {response.status_code}, Response: {response.text}")


def test_encadrant_login():
    """Test encadrant login (verify Auth creation)."""
    if 'encadrant_email' not in test_data:
        print("⚠️ Skipping Encadrant Login (No encadrant created)")
        return

    data = {
        "email": test_data['encadrant_email'],
        "password": test_data['encadrant_password']
    }
    response = requests.post(f"{AUTH_URL}/login", json=data)
    
    if response.status_code == 200:
        print(f"✅ PASS | Encadrant Login Successful")
        test_data['encadrant_token'] = response.json()['access_token']
    else:
        print(f"❌ FAIL | Status: {response.status_code}, Response: {response.text}")



def test_get_current_user():
    """Test get current user endpoint."""
    print("\n" + "="*60)
    print("AUTH SERVICE - CURRENT USER")
    print("="*60)

    if test_data["admin_token"]:
        result = api_call("GET", "/auth/api/v1/users/me", token=test_data["admin_token"])
        log_test("Get Current User (Admin)", result is not None and "email" in result)
    else:
        log_test("Get Current User (Admin)", False, "No admin token")


def test_list_users():
    """Test list users (admin only)."""
    print("\n" + "="*60)
    print("AUTH SERVICE - LIST USERS (Admin)")
    print("="*60)

    if test_data["admin_token"]:
        result = api_call("GET", "/auth/api/v1/users", token=test_data["admin_token"])
        log_test("List Users (Admin)", result is not None)
    else:
        log_test("List Users (Admin)", False, "No admin token")


# ============================================
# PROFILE SERVICE TESTS
# ============================================

def test_create_establishment():
    """Create an establishment."""
    print("\n" + "="*60)
    print("PROFILE SERVICE - ESTABLISHMENT")
    print("="*60)

    if test_data["admin_token"]:
        establishment_data = {
            "name": f"CHU Test Hospital {uuid.uuid4().hex[:4]}",
            "type": "CHU",
            "address": "123 Medical Street",
            "city": "Casablanca",
            "phone": "+212 5 22 00 00 00",
            "email": "contact@chu-test.ma"
        }
        result = api_call(
            "POST", "/profile/api/establishments/",
            token=test_data["admin_token"],
            data=establishment_data,
            expected_status=201
        )
        if result and "id" in result:
            test_data["establishment_id"] = result["id"]
            log_test("Create Establishment", True)
        else:
            log_test("Create Establishment", False)
    else:
        log_test("Create Establishment", False, "No admin token")


def test_create_service():
    """Create a service within an establishment."""
    if test_data["admin_token"] and test_data["establishment_id"]:
        service_data = {
            "name": f"Cardiology {uuid.uuid4().hex[:4]}",
            "establishment": test_data["establishment_id"],
            "description": "Cardiology Department"
        }
        result = api_call(
            "POST", "/profile/api/services/",
            token=test_data["admin_token"],
            data=service_data,
            expected_status=201
        )
        if result and "id" in result:
            test_data["service_id"] = result["id"]
            log_test("Create Service", True)
        else:
            log_test("Create Service", False)
    else:
        log_test("Create Service", False, "Missing establishment or token")


def test_create_student_profile():
    """Create a student profile."""
    print("\n" + "="*60)
    print("PROFILE SERVICE - STUDENT PROFILE")
    print("="*60)

    if test_data["student_user"] and test_data["admin_token"]:
        student_profile_data = {
            "user_id": test_data["student_user"].get("id"),
            "email": test_data["student_user"].get("email"),
            "first_name": "Test",
            "last_name": "Student",
            "cne": f"S{uuid.uuid4().hex[:8].upper()}",
            "cin": f"AB{uuid.uuid4().hex[:6].upper()}",
            "phone": "+212 6 00 00 00 01",
            "filiere": "Medicine",
            "niveau": 4
        }
        result = api_call(
            "POST", "/profile/api/students/",
            token=test_data["admin_token"],
            data=student_profile_data,
            expected_status=201
        )
        if result and "id" in result:
            test_data["student_profile_id"] = result["id"]
            log_test("Create Student Profile", True)
        else:
            log_test("Create Student Profile", False)
    else:
        log_test("Create Student Profile", False, "Missing student user or admin token")


def test_create_student_profile():
    """Create a student profile (Sync Auth)."""
    print("\n" + "="*60)
    print("PROFILE SERVICE - STUDENT PROFILE")
    print("="*60)

    # Needs Admin Token
    if 'admin_token' not in test_data:
         test_admin_login()
    
    headers = {"Authorization": f"Bearer {test_data.get('admin_token')}"}
    
    email = f"student_{uuid.uuid4().hex[:6]}@medtrack.com"
    password = "password123"
    
    data = {
        "email": email,
        "password": password,
        "first_name": "Student",
        "last_name": "Test",
        "cin": f"C{uuid.uuid4().hex[:6].upper()}",
        "phone": "0600000000",
        "student_number": f"ST{uuid.uuid4().hex[:6].upper()}",
        "date_of_birth": "2000-01-01",
        "university": "Med School",
        "program": "Medicine",
        "year_level": 3
    }
    
    response = requests.post(f"{PROFILE_URL}/api/students/", json=data, headers=headers)
    
    if response.status_code == 201:
        profile = response.json()
        print(f"✅ PASS | Student Profile Created: {profile['id']} (User ID: {profile['user_id']})")
        test_data["student_profile_id"] = profile['id']
        test_data["student_user"] = {'id': profile['user_id']} # Store basic user info
        test_data["student_email"] = email
        test_data["student_password"] = password
        log_test("Create Student Profile", True)
    else:
        print(f"❌ FAIL | Status: {response.status_code}, Response: {response.text}")
        log_test("Create Student Profile", False)


def test_create_encadrant_profile():
    """Create an encadrant profile (Sync Auth)."""
    print("\n" + "="*60)
    print("PROFILE SERVICE - ENCADRANT PROFILE")
    print("="*60)

    headers = {"Authorization": f"Bearer {test_data.get('admin_token')}"}
    
    email = f"encadrant_{uuid.uuid4().hex[:6]}@medtrack.com"
    password = "password123"
    
    data = {
        "email": email,
        "password": password,
        "first_name": "Dr.",
        "last_name": "Encadrant",
        "cin": f"CD{uuid.uuid4().hex[:6].upper()}",
        "phone": "+212 6 00 00 00 02",
        "speciality": "Cardiology",
        "position": "Professor",
        "establishment": test_data.get('establishment_id'),
        "service": test_data.get('service_id')
    }
    
    response = requests.post(f"{PROFILE_URL}/api/encadrants/", json=data, headers=headers)
    
    if response.status_code == 201:
        profile = response.json()
        print(f"✅ PASS | Encadrant Profile Created: {profile['id']}")
        test_data["encadrant_profile_id"] = profile['id']
        test_data["encadrant_user"] = {'id': profile['user_id']}
        test_data["encadrant_email"] = email
        test_data["encadrant_password"] = password
        log_test("Create Encadrant Profile", True)
    else:
        print(f"❌ FAIL | Status: {response.status_code}, Response: {response.text}")
        log_test("Create Encadrant Profile", False)


def test_list_students():
    """List all students."""
    if test_data["admin_token"]:
        result = api_call("GET", "/profile/api/students/", token=test_data["admin_token"])
        log_test("List Students", result is not None)
    else:
        log_test("List Students", False, "No admin token")


def test_list_encadrants():
    """List all encadrants."""
    if test_data["admin_token"]:
        result = api_call("GET", "/profile/api/encadrants/", token=test_data["admin_token"])
        log_test("List Encadrants", result is not None)
    else:
        log_test("List Encadrants", False, "No admin token")


# ============================================
# CORE SERVICE TESTS
# ============================================

def test_create_offer():
    """Create an internship offer."""
    print("\n" + "="*60)
    print("CORE SERVICE - OFFERS")
    print("="*60)

    if test_data["admin_token"] and test_data["service_id"]:
        offer_data = {
            "title": f"Cardiology Internship {uuid.uuid4().hex[:4]}",
            "description": "6-month internship in cardiology department",
            "service_id": test_data["service_id"],
            "start_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
            "capacity": 5,
            "requirements": "4th year medical student",
            "status": "published"
        }
        result = api_call(
            "POST", "/core/offers/",
            token=test_data["admin_token"],
            data=offer_data,
            expected_status=201
        )
        if result and "id" in result:
            test_data["offer_id"] = result["id"]
            log_test("Create Offer", True)
        else:
            log_test("Create Offer", False)
    else:
        log_test("Create Offer", False, "Missing admin token or service")


def test_list_offers():
    """List all offers."""
    if test_data["admin_token"]:
        result = api_call("GET", "/core/offers/", token=test_data["admin_token"])
        log_test("List Offers", result is not None)
    else:
        log_test("List Offers", False, "No token")


def test_get_offer_detail():
    """Get offer detail."""
    if test_data["offer_id"] and test_data["student_token"]:
        result = api_call("GET", f"/core/offers/{test_data['offer_id']}/", token=test_data["student_token"])
        log_test("Get Offer Detail", result is not None and "id" in result)
    else:
        log_test("Get Offer Detail", False, "No offer created or token")


# ============================================
# CORE SERVICE - APPLICATIONS
# ============================================
def test_apply_offer():
    """Student applies to an offer."""
    if test_data["offer_id"] and test_data["student_token"]:
        data = {
            "offer_id": test_data["offer_id"],
            "motivation": "I am very interested in this internship."
        }
        result = api_call("POST", "/core/applications/", data=data, token=test_data["student_token"], expected_status=201)
        if result and "id" in result:
            test_data["application_id"] = result["id"]
            log_test("Apply to Offer", True)
        else:
            log_test("Apply to Offer", False, "Failed to create application")
    else:
        log_test("Apply to Offer", False, "Missing offer_id or student_token")

def test_list_applications():
    """List applications (Admin)."""
    if test_data["admin_token"]:
        result = api_call("GET", "/core/applications/", token=test_data["admin_token"])
        log_test("List Applications", result is not None and "results" in result)
    else:
        log_test("List Applications", False, "Missing admin_token")

def test_accept_application():
    """Accept an application (Admin)."""
    if test_data.get("application_id") and test_data["admin_token"]:
        data = {"status": "accepted"}
        result = api_call("PATCH", f"/core/applications/{test_data['application_id']}/status/", data=data, token=test_data["admin_token"])
        log_test("Accept Application", result is not None and result.get("status") == "accepted")
    else:
        log_test("Accept Application", False, "Missing application_id or admin_token")


# ============================================
# COMM SERVICE TESTS
# ============================================

def test_send_message():
    """Send a message between users."""
    print("\n" + "="*60)
    print("COMM SERVICE - MESSAGES")
    print("="*60)

    if test_data["admin_token"] and test_data["student_user"] and test_data["admin_user"]:
        message_data = {
            "sender_id": test_data["admin_user"].get("id"),
            "receiver_id": test_data["student_user"].get("id"),
            "subject": "Welcome to MedTrack",
            "content": "Welcome! Your registration has been approved."
        }
        result = api_call(
            "POST", "/comm/api/messages/",
            token=test_data["admin_token"],
            data=message_data,
            expected_status=200
        )
        if result and "id" in result:
            test_data["message_id"] = result["id"]
            log_test("Send Message", True)
        else:
            log_test("Send Message", False)
    else:
        log_test("Send Message", False, "Missing tokens")


def test_list_messages():
    """List received messages."""
    if test_data["student_token"]:
        result = api_call("GET", "/comm/api/messages/", token=test_data["student_token"])
        log_test("List Messages", result is not None)
    else:
        log_test("List Messages", False, "No student token")


def test_create_notification():
    """Create a notification."""
    print("\n" + "="*60)
    print("COMM SERVICE - NOTIFICATIONS")
    print("="*60)

    if test_data["admin_token"] and test_data["student_user"]:
        notification_data = {
            "user_id": test_data["student_user"].get("id"),
            "title": "New Internship Available",
            "content": "A new cardiology internship matching your profile is now available.",
            "type": "system"
        }
        result = api_call(
            "POST", "/comm/api/notifications/",
            token=test_data["admin_token"],
            data=notification_data,
            expected_status=200
        )
        if result and "id" in result:
            test_data["notification_id"] = result["id"]
            log_test("Create Notification", True)
        else:
            log_test("Create Notification", False)
    else:
        log_test("Create Notification", False, "Missing tokens")


def test_list_notifications():
    """List user notifications."""
    if test_data["student_token"]:
        result = api_call("GET", "/comm/api/notifications/", token=test_data["student_token"])
        log_test("List Notifications", result is not None)
    else:
        log_test("List Notifications", False, "No student token")


# ============================================
# RUN ALL TESTS
# ============================================

def run_all_tests():
    """Run all API tests."""
    print("\n" + "="*60)
    print("MEDTRACK API INTEGRATION TESTS")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*60)

    # Health checks


    # Auth tests (Bootstrap)
    test_bootstrap_admin()
    test_admin_login()
    
    test_get_current_user()
    test_list_users()

    # Health checks (authenticated)
    test_health_checks()

    # Profile tests
    test_create_establishment()
    test_create_service()
    
    # Sync Creation & Login Verification
    test_create_student_profile()
    test_student_login()
    
    test_create_encadrant_profile()
    test_encadrant_login()
    
    test_list_students()
    test_list_encadrants()

    # Core tests
    test_create_offer()
    test_list_offers()
    test_get_offer_detail()

    # Application tests
    test_apply_offer()
    test_list_applications()
    test_accept_application()

    # Comm tests
    test_send_message()
    test_list_messages()
    test_create_notification()
    test_list_notifications()

    print("\n" + "="*60)
    print("TEST RUN COMPLETE")
    print("="*60)
    print("\nTest Data Summary:")
    for key, value in test_data.items():
        if value:
            if "token" in key:
                print(f"  {key}: [TOKEN PRESENT]")
            elif isinstance(value, dict):
                print(f"  {key}: {value.get('id', value.get('email', 'present'))}")
            else:
                print(f"  {key}: {value}")


if __name__ == "__main__":
    run_all_tests()
