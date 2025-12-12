"""Service client for inter-service communication via Consul."""
import os
import consul
import requests
from typing import Optional, Dict, Any


class ConsulServiceDiscovery:
    """Service discovery using Consul."""
    
    def __init__(self):
        self.consul_host = os.environ.get('CONSUL_HOST', 'consul')
        self.consul_port = int(os.environ.get('CONSUL_PORT', '8500'))
        self.consul_client = consul.Consul(host=self.consul_host, port=self.consul_port)
    
    def get_service_address(self, service_name: str) -> Optional[str]:
        """Get service address from Consul."""
        try:
            _, services = self.consul_client.health.service(service_name, passing=True)
            if services:
                service = services[0]
                address = service['Service']['Address']
                port = service['Service']['Port']
                return f"http://{address}:{port}"
        except Exception as e:
            print(f"Error discovering service {service_name}: {e}")
        return None


class ServiceClient:
    """Base client for service communication."""
    
    def __init__(self, service_name: str):
        self.discovery = ConsulServiceDiscovery()
        self.service_name = service_name
        self.base_url = None
    
    def _get_base_url(self) -> Optional[str]:
        """Get or refresh base URL."""
        if not self.base_url:
            self.base_url = self.discovery.get_service_address(self.service_name)
        return self.base_url
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """Make HTTP request to service."""
        base_url = self._get_base_url()
        if not base_url:
            print(f"Service {self.service_name} not available")
            return None
        
        url = f"{base_url}{endpoint}"
        try:
            response = requests.request(method, url, timeout=5, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling {self.service_name} at {url}: {e}")
            return None


class ProfileServiceClient(ServiceClient):
    """Client for PROFILE-SERVICE."""
    
    def __init__(self):
        super().__init__(os.environ.get('PROFILE_SERVICE_NAME', 'profile-service'))
    
    def get_student_details(self, student_id: str) -> Optional[Dict[Any, Any]]:
        """Get student details by ID."""
        return self._make_request('GET', f"/students/{student_id}")
    
    def get_service_details(self, service_id: str) -> Optional[Dict[Any, Any]]:
        """Get service details by ID."""
        return self._make_request('GET', f"/services/{service_id}")
    
    def get_establishment_details(self, establishment_id: str) -> Optional[Dict[Any, Any]]:
        """Get establishment details by ID."""
        return self._make_request('GET', f"/establishments/{establishment_id}")


class AuthServiceClient(ServiceClient):
    """Client for AUTH-SERVICE."""
    
    def __init__(self):
        super().__init__(os.environ.get('AUTH_SERVICE_NAME', 'auth-service'))
    
    def get_user_details(self, user_id: str) -> Optional[Dict[Any, Any]]:
        """Get user details by ID."""
        return self._make_request('GET', f"/users/{user_id}")


class CoreServiceClient(ServiceClient):
    """Client for CORE-SERVICE."""
    
    def __init__(self):
        super().__init__(os.environ.get('CORE_SERVICE_NAME', 'core-service'))
    
    def get_offer_details(self, offer_id: str) -> Optional[Dict[Any, Any]]:
        """Get offer details by ID."""
        return self._make_request('GET', f"/core/offers/{offer_id}")


# Singleton instances
_profile_client = None
_auth_client = None
_core_client = None


def get_profile_client() -> ProfileServiceClient:
    """Get singleton ProfileServiceClient."""
    global _profile_client
    if _profile_client is None:
        _profile_client = ProfileServiceClient()
    return _profile_client


def get_auth_client() -> AuthServiceClient:
    """Get singleton AuthServiceClient."""
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthServiceClient()
    return _auth_client


def get_core_client() -> CoreServiceClient:
    """Get singleton CoreServiceClient."""
    global _core_client
    if _core_client is None:
        _core_client = CoreServiceClient()
    return _core_client
