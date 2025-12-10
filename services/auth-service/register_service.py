#!/usr/bin/env python
"""
Register service with Consul on startup.
"""
import os
import json
import time
import requests


def register_service():
    """Register this service with Consul."""
    consul_host = os.environ.get('CONSUL_HOST', 'consul')
    consul_port = os.environ.get('CONSUL_PORT', '8500')
    service_name = os.environ.get('SERVICE_NAME', 'auth-service')
    
    # Load service configuration
    config_path = os.path.join(os.path.dirname(__file__), 'consul', 'service.json')
    
    with open(config_path, 'r') as f:
        service_config = json.load(f)
    
    # Update service config with environment values
    service_config['service']['name'] = service_name
    service_config['service']['id'] = f"{service_name}-{os.environ.get('HOSTNAME', '1')}"
    
    consul_url = f"http://{consul_host}:{consul_port}/v1/agent/service/register"
    
    # Retry logic for Consul registration
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.put(
                consul_url,
                json=service_config['service'],
                timeout=10
            )
            if response.status_code == 200:
                print(f"Successfully registered {service_name} with Consul")
                return True
            else:
                print(f"Failed to register with Consul: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries}: Could not connect to Consul: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2)
    
    print("Warning: Could not register with Consul after all retries")
    return False


if __name__ == '__main__':
    register_service()
