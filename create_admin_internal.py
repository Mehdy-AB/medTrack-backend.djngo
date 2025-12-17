import os
import django
import sys

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from users.models import User

email = 'admin@medtrack.com'
password = 'password123'

try:
    u, created = User.objects.get_or_create(email=email, defaults={
        'role': 'admin', 
        'is_active': True, 
        'first_name': 'Admin'
    })
    u.set_password(password)
    u.role = 'admin'
    u.save()
    print(f"User {email} created/updated successfully.")
except Exception as e:
    print(f"Error: {e}")
