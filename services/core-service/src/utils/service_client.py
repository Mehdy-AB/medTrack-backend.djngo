"""Service client utilities for cross-service communication via Consul."""
import os
import requests
import consul
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ConsulServiceDiscovery:
    """Consul service discovery client with Docker DNS fallback."""
    
    def __init__(self):
        self.consul_host = os.environ.get('CONSUL_HOST', 'consul')
        self.consul_port = int(os.environ.get('CONSUL_PORT', 8500))
        try:
            self.client = consul.Consul(host=self.consul_host, port=self.consul_port)
            logger.info(f"✅ Consul client initialized at {self.consul_host}:{self.consul_port}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Consul client: {e}")
            self.client = None
    
    def get_service_url(self, service_name: str) -> str:
        """
        Get service URL from Consul with Docker DNS fallback.
        
        Args:
            service_name: Name of the service (e.g., 'auth-service')
            
        Returns:
            Service URL (e.g., 'http://auth-service:8000')
        """
        if not self.client:
            logger.warning(f"⚠️ Consul client not available, using Docker DNS for {service_name}")
            return f"http://{service_name}:8000"
        
        try:
            _, services = self.client.health.service(service_name, passing=True)
            if services:
                entry = services[0]
                port = entry['Service']['Port']
                
                # ALWAYS use service name for Docker DNS (never trust IPs from Consul)
                # Docker's internal DNS will resolve to the correct IP dynamically
                url = f"http://{service_name}:{port}"
                
                logger.info(f"✅ Discovered {service_name} via Consul, using Docker DNS: {url}")
                return url
            else:
                logger.warning(f"⚠️ No healthy instances for {service_name} in Consul, using Docker DNS fallback")
        except Exception as e:
            logger.warning(f"⚠️ Consul discovery error for {service_name}: {e}")
        
        # Fallback to Docker DNS
        logger.info(f"Using Docker DNS fallback for {service_name}")
        return f"http://{service_name}:8000"


# Initialize global Consul discovery client
_consul = ConsulServiceDiscovery()


class ServiceClient:
    """Base class for all service clients."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.base_url = None
    
    def _get_base_url(self) -> str:
        """Get or refresh base URL from Consul."""
        if not self.base_url:
            self.base_url = _consul.get_service_url(self.service_name)
        return self.base_url
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to service.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON data or None if request fails
        """
        base_url = self._get_base_url()
        url = f"{base_url}{endpoint}"
        
        try:
            response = requests.request(method, url, timeout=5, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to call {self.service_name} at {url}: {e}")
            return None


class AuthServiceClient(ServiceClient):
    """Client for AUTH-SERVICE."""
    
    def __init__(self):
        super().__init__(os.environ.get('AUTH_SERVICE_NAME', 'auth-service'))
    
    def get_user_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user (encadrant) details by ID."""
        return self._make_request('GET', f"/auth/api/v1/users/{user_id}")


class ProfileServiceClient(ServiceClient):
    """Client for PROFILE-SERVICE."""
    
    def __init__(self):
        super().__init__(os.environ.get('PROFILE_SERVICE_NAME', 'profile-service'))
    
    def get_service_details(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get service details by ID."""
        return self._make_request('GET', f"/profile/api/services/{service_id}/")
    
    def get_establishment_details(self, establishment_id: str) -> Optional[Dict[str, Any]]:
        """Get establishment details by ID."""
        return self._make_request('GET', f"/profile/api/establishments/{establishment_id}/")
    
    def get_student_details(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get student details by ID."""
        return self._make_request('GET', f"/profile/api/students/{student_id}/")
    
    def get_encadrant_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get encadrant details by user ID."""
        return self._make_request('GET', f"/profile/api/encadrants/by_user/{user_id}/")


# Singleton instances
_auth_client = None
_profile_client = None


def get_auth_client() -> AuthServiceClient:
    """Get singleton AuthServiceClient."""
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthServiceClient()
    return _auth_client


def get_profile_client() -> ProfileServiceClient:
    """Get singleton ProfileServiceClient."""
    global _profile_client
    if _profile_client is None:
        _profile_client = ProfileServiceClient()
    return _profile_client
