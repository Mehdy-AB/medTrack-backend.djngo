"""
Service client to call other microservices (e.g., AUTH-SERVICE)
Uses Consul for service discovery
"""
import requests
import logging
import consul
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ConsulServiceDiscovery:
    """Consul service discovery client"""

    def __init__(self):
        self.consul_host = os.environ.get('CONSUL_HOST', 'consul')
        self.consul_port = int(os.environ.get('CONSUL_PORT', 8500))
        self.client = consul.Consul(host=self.consul_host, port=self.consul_port)

    def get_service_url(self, service_name: str, fallback_url: str = None) -> str:
        """
        Get service URL from Consul

        Args:
            service_name: Name of the service (e.g., 'auth-service')
            fallback_url: Fallback URL if Consul is unavailable

        Returns:
            Service URL (e.g., 'http://auth-service:8000')
        """
        try:
            _, services = self.client.health.service(service_name, passing=True)
            if services:
                entry = services[0]
                address = entry['Service'].get('Address') or entry['Node']['Address']
                port = entry['Service']['Port']
                url = f"http://{address}:{port}"
                logger.debug(f"✅ Discovered {service_name} at {url} via Consul")
                return url
            else:
                logger.warning(f"⚠️  No healthy instances for {service_name} in Consul")
        except Exception as e:
            logger.warning(f"⚠️  Consul unavailable: {e}")

        # Fallback to hardcoded URL
        if fallback_url:
            logger.info(f"Using fallback URL for {service_name}: {fallback_url}")
            return fallback_url

        # Default fallback pattern
        return f"http://{service_name}:8000"


# Initialize Consul client
_consul = ConsulServiceDiscovery()


class AuthServiceClient:
    """Client to interact with AUTH-SERVICE via Consul service discovery"""

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from AUTH-SERVICE by user_id
        Uses Consul to discover AUTH-SERVICE URL
        API ENDPOINT: GET /auth/api/v1/users/me (with X-User-ID header)
        """
        try:
            # Discover AUTH-SERVICE via Consul
            auth_url = _consul.get_service_url('auth-service', 'http://auth-service:8000')

            response = requests.get(
                f"{auth_url}/auth/api/v1/users/me",
                headers={'X-User-ID': user_id},
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
    def get_users_by_role(role: str) -> list[Dict[str, Any]]:
        """
        Get all users with a specific role from AUTH-SERVICE
        REAL API CALL: GET {AUTH_SERVICE_URL}/auth/api/v1/users?role={role}
        """
        try:
            response = requests.get(
                f"{AUTH_SERVICE_URL}/auth/api/v1/users",
                params={"role": role},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                # Handle paginated response
                return data.get('results', data) if isinstance(data, dict) else data
            else:
                logger.warning(f"AUTH-SERVICE returned {response.status_code} for role {role}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call AUTH-SERVICE for role {role}: {e}")
            return []

    @staticmethod
    def verify_user_exists(user_id: str) -> bool:
        """
        Verify if a user exists in AUTH-SERVICE
        REAL API CALL: GET {AUTH_SERVICE_URL}/auth/api/v1/users/{user_id}
        """
        try:
            auth_url = 'http://auth-service:8000'
            # auth_url = _consul.get_service_url('auth-service', 'http://auth-service:8000')
            response = requests.get(
                f"{auth_url}/auth/api/v1/users/{user_id}",
                timeout=5
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def create_user(user_data: Dict[str, Any], token: str) -> Optional[Dict[str, Any]]:
        """
        Create a new user in AUTH-SERVICE
        API ENDPOINT: POST /auth/api/v1/users
        Requires Admin/Encadrant token
        """
        try:
            # Force use of internal K8s/Docker DNS for reliability
            auth_url = "http://auth-service:8000"
            # auth_url = _consul.get_service_url('auth-service', 'http://auth-service:8000')
            
            headers = {
                'Authorization': token if token.startswith('Bearer ') else f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{auth_url}/auth/api/v1/users",
                json=user_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"✅ Created user {user_data.get('email')} in AUTH-SERVICE")
                return response.json()
            else:
                logger.warning(f"Failed to create user in AUTH-SERVICE. Status: {response.status_code}, Body: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call AUTH-SERVICE create_user: {e}")
            return None


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
