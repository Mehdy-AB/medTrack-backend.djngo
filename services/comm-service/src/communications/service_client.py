"""
Service client to call other microservices (AUTH-SERVICE, PROFILE-SERVICE, CORE-SERVICE)
Uses Consul for service discovery with fallback to static URLs
"""
import requests
import logging
import consul
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# Fallback URLs (used if Consul is unavailable)
AUTH_SERVICE_FALLBACK = "http://auth-service:8000"
PROFILE_SERVICE_FALLBACK = "http://profile-service:8000"
CORE_SERVICE_FALLBACK = "http://core-service:8000"


# ============================================
# CONSUL SERVICE DISCOVERY
# ============================================

class ConsulServiceDiscovery:
    """
    Service discovery using Consul
    Dynamically resolves service URLs from Consul registry
    """

    def __init__(self):
        try:
            self.client = consul.Consul(
                host=settings.CONSUL_HOST,
                port=settings.CONSUL_PORT
            )
            logger.info(f"✅ Consul client initialized: {settings.CONSUL_HOST}:{settings.CONSUL_PORT}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize Consul client: {e}")
            self.client = None

    def get_service_url(self, service_name: str, fallback_url: str = None) -> str:
        """
        Get service URL from Consul, with fallback to static URL

        Args:
            service_name: Name of service in Consul (e.g., 'auth-service')
            fallback_url: URL to use if Consul lookup fails

        Returns:
            Service URL (http://host:port)
        """
        if not self.client:
            logger.debug(f"Consul unavailable, using fallback URL for {service_name}")
            return fallback_url or f"http://{service_name}:8000"

        try:
            # Query Consul for healthy service instances
            _, services = self.client.health.service(service_name, passing=True)

            if services:
                # Use first healthy instance
                service = services[0]['Service']
                url = f"http://{service['Address']}:{service['Port']}"
                logger.debug(f"📡 Resolved {service_name} via Consul: {url}")
                return url
            else:
                logger.warning(f"⚠️  No healthy instances of {service_name} in Consul")
                return fallback_url or f"http://{service_name}:8000"

        except Exception as e:
            logger.warning(f"⚠️  Consul lookup failed for {service_name}: {e}")
            return fallback_url or f"http://{service_name}:8000"


# Global Consul client instance
_consul_discovery = ConsulServiceDiscovery()


def get_auth_service_url() -> str:
    """Get AUTH-SERVICE URL from Consul with fallback"""
    return _consul_discovery.get_service_url('auth-service', AUTH_SERVICE_FALLBACK)


def get_profile_service_url() -> str:
    """Get PROFILE-SERVICE URL from Consul with fallback"""
    return _consul_discovery.get_service_url('profile-service', PROFILE_SERVICE_FALLBACK)


def get_core_service_url() -> str:
    """Get CORE-SERVICE URL from Consul with fallback"""
    return _consul_discovery.get_service_url('core-service', CORE_SERVICE_FALLBACK)


class AuthServiceClient:
    """Client to interact with AUTH-SERVICE"""

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from AUTH-SERVICE by user_id
        REAL API CALL: GET {AUTH_SERVICE_URL}/auth/api/v1/users/{user_id}
        """
        try:
            auth_url = get_auth_service_url()
            response = requests.get(
                f"{auth_url}/auth/api/v1/users/{user_id}",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"AUTH-SERVICE returned {response.status_code} for user {user_id}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call AUTH-SERVICE for user {user_id}: {e}")
            return None

    @staticmethod
    def get_users_by_ids(user_ids: list[str]) -> list[Dict[str, Any]]:
        """
        Get multiple users by IDs from AUTH-SERVICE

        Since AUTH-SERVICE doesn't have a bulk endpoint, we fetch individually
        (or you can add a bulk endpoint to AUTH-SERVICE later)
        """
        users = []
        for user_id in user_ids:
            user = AuthServiceClient.get_user_by_id(user_id)
            if user:
                users.append(user)
        return users


class ProfileServiceClient:
    """Client to interact with PROFILE-SERVICE (REAL HTTP CALLS)"""

    @staticmethod
    def get_student_by_id(student_id: str) -> Optional[Dict[str, Any]]:
        """
        Get student data from PROFILE-SERVICE by student_id
        REAL API CALL: GET {PROFILE_SERVICE_URL}/profile/api/students/{student_id}/
        """
        try:
            profile_url = get_profile_service_url()
            response = requests.get(
                f"{profile_url}/profile/api/students/{student_id}/",
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
            profile_url = get_profile_service_url()
            response = requests.get(
                f"{profile_url}/profile/api/students/by_user/{user_id}/",
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
            profile_url = get_profile_service_url()
            response = requests.get(
                f"{profile_url}/profile/api/encadrants/{encadrant_id}/",
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
            profile_url = get_profile_service_url()
            response = requests.get(
                f"{profile_url}/profile/api/establishments/{establishment_id}/",
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
