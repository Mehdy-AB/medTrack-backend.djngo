#!/usr/bin/env python3
"""
MedTrack Database Seeder
====================================
Populates the database with initial data for development/demo.

Usage:
    python seed_data.py
"""

import requests
import json
import uuid
import time
import subprocess
from datetime import datetime, timedelta

import os

# Configuration
BASE_URL = os.environ.get("API_GATEWAY_URL", "http://localhost")
AUTH_URL = f"{BASE_URL}/auth/api/v1"
PROFILE_URL = f"{BASE_URL}/profile/api"
CORE_URL = f"{BASE_URL}/core"

# Data
data_store = {}

def log(msg, success=True):
    icon = "✅" if success else "❌"
    print(f"{icon} {msg}")

def wait_for_services():
    print("⏳ Waiting for services to be ready...")
    endpoints = [
        f"{BASE_URL}/auth/health",
        f"{BASE_URL}/profile/health",
        f"{BASE_URL}/core/health",
    ]
    
    max_retries = 30
    for i in range(max_retries):
        try:
            all_ready = True
            for ep in endpoints:
                try:
                    res = requests.get(ep, timeout=2)
                    # 401/403 means service is up but protected, which is fine for readiness check
                    if res.status_code not in [200, 401, 403]:
                        all_ready = False
                        print(f"   {ep} returned {res.status_code}")
                        break
                except Exception as e:
                    all_ready = False
                    print(f"   {ep} unreachable: {e}")
                    break
            
            if all_ready:
                print("🚀 Services are ready!")
                return True
        except:
            pass
        
        time.sleep(2)
        print(f"   Waiting... ({i+1}/{max_retries})")
    
    return False

def create_admin():
    email = "admin@medtrack.com"
    password = "password123"
    
    # Try login first
    try:
        res = requests.post(f"{AUTH_URL}/login", json={"email": email, "password": password})
        if res.status_code == 200:
            log("Admin user already exists.")
            data_store['admin_token'] = res.json()['access_token']
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
        subprocess.run(cmd, check=True, capture_output=True)
        log("Admin user created.")
        
        # Login to get token
        res = requests.post(f"{AUTH_URL}/login", json={"email": email, "password": password})
        data_store['admin_token'] = res.json()['access_token']
    except Exception as e:
        log(f"Failed to create admin: {e}", False)

def seed_establishments():
    if 'admin_token' not in data_store: return

    headers = {"Authorization": f"Bearer {data_store['admin_token']}"}
    
    hospitals = [
        {
            "name": "CHU Mustapha Bacha",
            "type": "CHU",
            "address": "Place du 1er Mai, Alger",
            "city": "Alger",
            "phone": "021 23 55 55",
            "email": "contact@chu-mustapha.dz"
        },
        {
            "name": "EPH Kouba",
            "type": "EPH",
            "address": "Kouba, Alger",
            "city": "Alger",
            "phone": "021 28 33 33",
            "email": "contact@eph-kouba.dz"
        }
    ]

    for h in hospitals:
        res = requests.post(f"{PROFILE_URL}/establishments/", json=h, headers=headers)
        if res.status_code == 201:
            log(f"Created Hospital: {h['name']}")
            if h['name'] == "CHU Mustapha Bacha":
                data_store['chu_id'] = res.json()['id']
        else:
            log(f"Failed to create {h['name']}: {res.text}", False)

def seed_services():
    if 'admin_token' not in data_store or 'chu_id' not in data_store: return
    headers = {"Authorization": f"Bearer {data_store['admin_token']}"}

    services = [
        {"name": "Cardiologie", "description": "Service de cardiologie"},
        {"name": "Pédiatrie", "description": "Service de pédiatrie"},
        {"name": "Chirurgie Générale", "description": "Bloc opératoire central"},
    ]

    for s in services:
        s['establishment'] = data_store['chu_id']
        res = requests.post(f"{PROFILE_URL}/services/", json=s, headers=headers)
        if res.status_code == 201:
            log(f"Created Service: {s['name']}")
            data_store[f"service_{s['name']}"] = res.json()['id']
        elif res.status_code == 400 and "already exists" in res.text:
            log(f"Service {s['name']} already exists.")
        else:
            log(f"Failed to create service {s['name']}: {res.text}", False)

def seed_users():
    if 'admin_token' not in data_store: return
    headers = {"Authorization": f"Bearer {data_store['admin_token']}"}

    # Encadrant
    encadrant = {
        "email": "encadrant@medtrack.com",
        "password": "password123",
        "first_name": "Dr. Ahmed",
        "last_name": "Benali",
        "cin": "AB123456",
        "phone": "0661123456",
        "speciality": "Cardiologie",
        "position": "Maître Assistant",
        "establishment": data_store.get('chu_id'),
        "service": data_store.get('service_Cardiologie')
    }

    try:
        res = requests.post(f"{PROFILE_URL}/encadrants/", json=encadrant, headers=headers)
        if res.status_code == 201:
            log(f"Created Encadrant: {encadrant['first_name']} {encadrant['last_name']}")
        else:
            # Check if user exists but profile doesnt, or both exist. Simplified: fail quietly if duplicate
            log(f"Encadrant creation skipped or failed: {res.status_code}")
    except Exception as e:
        log(f"Encadrant creation error: {e}", False)

    # Student
    student = {
        "email": "student@medtrack.com",
        "password": "password123",
        "first_name": "Karim",
        "last_name": "Slimani",
        "cin": "CD987654",
        "student_number": "20230001",
        "phone": "0550123456",
        "date_of_birth": "2000-05-15",
        "university": "Faculté de Médecine d'Alger",
        "program": "Médecine",
        "year_level": 6
    }
    
    try:
        res = requests.post(f"{PROFILE_URL}/students/", json=student, headers=headers)
        if res.status_code == 201:
            log(f"Created Student: {student['first_name']} {student['last_name']}")
        else:
            log(f"Student creation skipped or failed: {res.status_code}")
    except Exception as e:
        log(f"Student creation error: {e}", False)

def seed_offers():
    if 'admin_token' not in data_store or 'service_Cardiologie' not in data_store: return
    headers = {"Authorization": f"Bearer {data_store['admin_token']}"}

    offer = {
        "title": "Stage Interné - Cardiologie",
        "description": "Stage pratique de 3 mois au service de cardiologie. Participation aux visites et gardes.",
        "service_id": data_store['service_Cardiologie'],
        "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=97)).strftime("%Y-%m-%d"),
        "capacity": 4,
        "requirements": "6ème année médecine",
        "status": "published"
    }

    res = requests.post(f"{CORE_URL}/offers/", json=offer, headers=headers)
    if res.status_code == 201:
        log(f"Created Offer: {offer['title']}")
    else:
        log(f"Offer creation skipped or failed: {res.status_code}")

def run_seed():
    print("\n🌱 Starting Database Seeding...\n")
    if wait_for_services():
        create_admin()
        seed_establishments()
        seed_services()
        seed_users()
        seed_offers()
        print("\n✨ Seeding Complete!")
    else:
        print("\n❌ Services did not become ready. Aborting.")

if __name__ == "__main__":
    run_seed()
