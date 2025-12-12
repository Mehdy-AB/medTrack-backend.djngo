"""
Service client to call other microservices (AUTH-SERVICE, PROFILE-SERVICE, CORE-SERVICE)
"""
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Internal Docker network URLs
AUTH_SERVICE_URL = "http://auth-service:8000"
PROFILE_SERVICE_URL = "http://profile-service:8000"
CORE_SERVICE_URL = "http://core-service:8000"


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
    def get_users_by_ids(user_ids: list[str]) -> list[Dict[str, Any]]:
        """
        Get multiple users by IDs from AUTH-SERVICE

        For now, returns mock data.
        Later: POST {AUTH_SERVICE_URL}/auth/api/users/bulk/ with body: {"user_ids": [...]}
        """
        # Mock data
        return [
            {
                "id": user_id,
                "email": f"user{user_id}@example.com",
                "first_name": "User",
                "last_name": f"#{i}",
                "role": "student"
            }
            for i, user_id in enumerate(user_ids)
        ]


class ProfileServiceClient:
    """Client to interact with PROFILE-SERVICE (REAL HTTP CALLS)"""

    @staticmethod
    def get_student_by_id(student_id: str) -> Optional[Dict[str, Any]]:
        """
        Get student data from PROFILE-SERVICE by student_id
        REAL API CALL: GET {PROFILE_SERVICE_URL}/profile/api/students/{student_id}/
        """
        try:
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile/api/students/{student_id}/",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"PROFILE-SERVICE returned {response.status_code} for student {student_id}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call PROFILE-SERVICE for student {student_id}: {e}")
            return None

    @staticmethod
    def get_student_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get student by user_id from PROFILE-SERVICE
        REAL API CALL: GET {PROFILE_SERVICE_URL}/profile/api/students/by_user/{user_id}/
        """
        try:
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile/api/students/by_user/{user_id}/",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"PROFILE-SERVICE returned {response.status_code} for user {user_id}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call PROFILE-SERVICE for user {user_id}: {e}")
            return None

    @staticmethod
    def get_encadrant_by_id(encadrant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get encadrant data from PROFILE-SERVICE
        REAL API CALL: GET {PROFILE_SERVICE_URL}/profile/api/encadrants/{encadrant_id}/
        """
        try:
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile/api/encadrants/{encadrant_id}/",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"PROFILE-SERVICE returned {response.status_code} for encadrant {encadrant_id}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call PROFILE-SERVICE for encadrant {encadrant_id}: {e}")
            return None

    @staticmethod
    def get_establishment_by_id(establishment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get establishment data from PROFILE-SERVICE
        REAL API CALL: GET {PROFILE_SERVICE_URL}/profile/api/establishments/{establishment_id}/
        """
        try:
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile/api/establishments/{establishment_id}/",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"PROFILE-SERVICE returned {response.status_code} for establishment {establishment_id}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call PROFILE-SERVICE for establishment {establishment_id}: {e}")
            return None


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
