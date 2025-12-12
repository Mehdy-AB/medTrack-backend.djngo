"""
Service client to call other microservices (e.g., AUTH-SERVICE)
"""
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Internal Docker network URLs
AUTH_SERVICE_URL = "http://auth-service:8000"


class AuthServiceClient:
    """Client to interact with AUTH-SERVICE"""

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from AUTH-SERVICE by user_id

        For now, returns mock data since AUTH-SERVICE is empty.
        Later, this will make actual HTTP call to: GET {AUTH_SERVICE_URL}/auth/api/users/{user_id}/
        """
        # TODO: Replace with actual API call when AUTH-SERVICE is ready
        # try:
        #     response = requests.get(
        #         f"{AUTH_SERVICE_URL}/auth/api/users/{user_id}/",
        #         timeout=5
        #     )
        #     if response.status_code == 200:
        #         return response.json()
        #     else:
        #         logger.error(f"AUTH-SERVICE returned {response.status_code}")
        #         return None
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Failed to call AUTH-SERVICE: {e}")
        #     return None

        # Mock data for now
        return {
            "id": user_id,
            "email": f"user{user_id}@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "role": "student",
            "is_active": True,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }

    @staticmethod
    def get_users_by_role(role: str) -> list[Dict[str, Any]]:
        """
        Get all users with a specific role from AUTH-SERVICE

        For now, returns mock data.
        Later: GET {AUTH_SERVICE_URL}/auth/api/users/?role={role}
        """
        # Mock data
        return [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "email": f"{role}1@example.com",
                "first_name": "Alice",
                "last_name": "Smith",
                "phone": "+1111111111",
                "role": role,
                "is_active": True
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "email": f"{role}2@example.com",
                "first_name": "Bob",
                "last_name": "Johnson",
                "phone": "+2222222222",
                "role": role,
                "is_active": True
            }
        ]

    @staticmethod
    def verify_user_exists(user_id: str) -> bool:
        """
        Verify if a user exists in AUTH-SERVICE

        For now, always returns True (mock).
        Later: HEAD {AUTH_SERVICE_URL}/auth/api/users/{user_id}/
        """
        # Mock: always return True
        return True


# Service URLs
PROFILE_SERVICE_URL = "http://profile-service:8000"
CORE_SERVICE_URL = "http://core-service:8000"


class ProfileServiceClient:
    """Client to interact with PROFILE-SERVICE"""

    @staticmethod
    def get_student_by_id(student_id: str) -> Optional[Dict[str, Any]]:
        """
        Get student data from PROFILE-SERVICE by student_id

        For now, returns mock data.
        Later: GET {PROFILE_SERVICE_URL}/profile/api/students/{student_id}/
        """
        # TODO: Replace with actual API call when needed
        # try:
        #     response = requests.get(
        #         f"{PROFILE_SERVICE_URL}/profile/api/students/{student_id}/",
        #         timeout=5
        #     )
        #     if response.status_code == 200:
        #         return response.json()
        #     return None
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Failed to call PROFILE-SERVICE: {e}")
        #     return None

        # Mock data
        return {
            "id": student_id,
            "user_id": "11111111-1111-1111-1111-111111111111",
            "student_number": "STU001",
            "university": "Mohammed V University",
            "program": "Medicine",
            "year_level": 3
        }

    @staticmethod
    def get_student_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get student by user_id from PROFILE-SERVICE

        For now, returns mock data.
        Later: GET {PROFILE_SERVICE_URL}/profile/api/students/by_user/{user_id}/
        """
        # Mock data
        return {
            "id": "student-uuid",
            "user_id": user_id,
            "student_number": "STU001",
            "university": "Mohammed V University",
            "program": "Medicine",
            "year_level": 3
        }

    @staticmethod
    def get_encadrant_by_id(encadrant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get encadrant data from PROFILE-SERVICE

        For now, returns mock data.
        Later: GET {PROFILE_SERVICE_URL}/profile/api/encadrants/{encadrant_id}/
        """
        # Mock data
        return {
            "id": encadrant_id,
            "user_id": "22222222-2222-2222-2222-222222222222",
            "position": "Senior Consultant",
            "specialty": "Cardiology"
        }

    @staticmethod
    def get_establishment_by_id(establishment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get establishment data from PROFILE-SERVICE

        For now, returns mock data.
        Later: GET {PROFILE_SERVICE_URL}/profile/api/establishments/{establishment_id}/
        """
        # Mock data
        return {
            "id": establishment_id,
            "name": "Hospital Central",
            "type": "Public Hospital",
            "city": "Casablanca"
        }


class CoreServiceClient:
    """Client to interact with CORE-SERVICE (for offers, stages, etc.)"""

    @staticmethod
    def get_offer_by_id(offer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get offer/stage data from CORE-SERVICE

        For now, returns mock data.
        Later: GET {CORE_SERVICE_URL}/core/api/offers/{offer_id}/
        """
        # TODO: Replace with actual API call when CORE-SERVICE is ready
        # try:
        #     response = requests.get(
        #         f"{CORE_SERVICE_URL}/core/api/offers/{offer_id}/",
        #         timeout=5
        #     )
        #     if response.status_code == 200:
        #         return response.json()
        #     return None
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Failed to call CORE-SERVICE: {e}")
        #     return None

        # Mock data
        return {
            "id": offer_id,
            "title": "Cardiology Internship",
            "establishment_id": "establishment-uuid",
            "service_id": "service-uuid",
            "duration_weeks": 12,
            "status": "active"
        }

    @staticmethod
    def get_stage_by_id(stage_id: str) -> Optional[Dict[str, Any]]:
        """
        Get stage (internship assignment) data from CORE-SERVICE

        For now, returns mock data.
        Later: GET {CORE_SERVICE_URL}/core/api/stages/{stage_id}/
        """
        # Mock data
        return {
            "id": stage_id,
            "student_id": "student-uuid",
            "offer_id": "offer-uuid",
            "encadrant_id": "encadrant-uuid",
            "start_date": "2025-01-15",
            "end_date": "2025-04-15",
            "status": "active"
        }


class CommServiceClient:
    """Client to interact with COMM-SERVICE (for notifications, messages, etc.)"""

    @staticmethod
    def send_notification(user_id: str, title: str, content: str, notification_type: str = "system") -> bool:
        """
        Send a notification via COMM-SERVICE

        For now, returns True (mock).
        Later: POST {COMM_SERVICE_URL}/comm/api/notifications/
        """
        # TODO: Replace with actual API call when COMM-SERVICE is ready
        # try:
        #     response = requests.post(
        #         f"http://comm-service:8000/comm/api/notifications/",
        #         json={
        #             "user_id": user_id,
        #             "type": notification_type,
        #             "title": title,
        #             "content": content
        #         },
        #         timeout=5
        #     )
        #     return response.status_code == 201
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Failed to call COMM-SERVICE: {e}")
        #     return False

        # Mock: always return True
        logger.info(f"Mock notification sent to user {user_id}: {title}")
        return True
