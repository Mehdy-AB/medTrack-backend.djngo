#!/usr/bin/env python
"""Register service with Consul on startup."""
import os
import json
import time
import requests

def register_service():
    consul_host = os.environ.get('CONSUL_HOST', 'consul')
    consul_port = os.environ.get('CONSUL_PORT', '8500')
    service_name = os.environ.get('SERVICE_NAME', 'profile-service')
    
    config_path = os.path.join(os.path.dirname(__file__), 'consul', 'service.json')
    with open(config_path, 'r') as f:
        service_config = json.load(f)
    
    service_config['service']['name'] = service_name
    service_config['service']['id'] = f"{service_name}-{os.environ.get('HOSTNAME', '1')}"
    
    consul_url = f"http://{consul_host}:{consul_port}/v1/agent/service/register"
    
    for attempt in range(5):
        try:
            response = requests.put(consul_url, json=service_config['service'], timeout=10)
            if response.status_code == 200:
                print(f"Successfully registered {service_name} with Consul")
                return True
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/5: Could not connect to Consul: {e}")
        if attempt < 4:
            time.sleep(2)
    
    print("Warning: Could not register with Consul after all retries")
    return False

if __name__ == '__main__':
    register_service()
