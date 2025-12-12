"""Service client utilities for cross-service communication via Consul."""
import os
import requests
import consul
from typing import Optional, Dict, Any
from functools import lru_cache


class ConsulServiceDiscovery:
    """Consul service discovery client."""
    
    def __init__(self):
        consul_host = os.environ.get('CONSUL_HOST', 'consul')
        consul_port = int(os.environ.get('CONSUL_PORT', '8500'))
        self.consul_client = consul.Consul(host=consul_host, port=consul_port)
    
    @lru_cache(maxsize=100)
    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get service URL from Consul."""
        try:
            _, services = self.consul_client.health.service(service_name, passing=True)
            if services:
                # Get first healthy instance
                service = services[0]['Service']
                address = service['Address']
                port = service['Port']
                return f"http://{address}:{port}"
        except Exception as e:
            print(f"Error discovering service {service_name}: {e}")
        return None


class ServiceClient:
    """Base class for making HTTP calls to other services."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.discovery = ConsulServiceDiscovery()
        self.timeout = 5  # seconds
    
    def _get_service_url(self) -> Optional[str]:
        """Get the service URL from Consul."""
        return self.discovery.get_service_url(self.service_name)
    
    def _make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Optional[Dict[Any, Any]]:
        """Make HTTP request to service."""
        service_url = self._get_service_url()
        if not service_url:
            print(f"Could not discover {self.service_name}")
            return None
        
        url = f"{service_url}{endpoint}"
        try:
            response = requests.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"Error calling {url}: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request to {url} failed: {e}")
            return None


class AuthServiceClient(ServiceClient):
    """Client for AUTH-SERVICE."""
    
    def __init__(self):
        # Try common service names
        service_name = os.environ.get('AUTH_SERVICE_NAME', 'auth-service')
        super().__init__(service_name)
    
    def get_user_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user (encadrant) details by ID."""
        return self._make_request(f"/users/{user_id}")


class ProfileServiceClient(ServiceClient):
    """Client for PROFILE-SERVICE."""
    
    def __init__(self):
        service_name = os.environ.get('PROFILE_SERVICE_NAME', 'profile-service')
        super().__init__(service_name)
    
    def get_service_details(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get service details by ID."""
        return self._make_request(f"/services/{service_id}")
    
    def get_establishment_details(self, establishment_id: str) -> Optional[Dict[str, Any]]:
        """Get establishment details by ID."""
        return self._make_request(f"/establishments/{establishment_id}")
    
    def get_student_details(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get student details by ID."""
        return self._make_request(f"/students/{student_id}")



# Singleton instances
_auth_client = None
_profile_client = None


def get_auth_client() -> AuthServiceClient:
    """Get singleton AUTH-SERVICE client."""
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthServiceClient()
    return _auth_client


def get_profile_client() -> ProfileServiceClient:
    """Get singleton PROFILE-SERVICE client."""
    global _profile_client
    if _profile_client is None:
        _profile_client = ProfileServiceClient()
    return _profile_client
