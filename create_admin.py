"""
Simple script to create an admin user via the backend API
"""
import requests

# Backend URL
BACKEND_URL = "https://rmi-audit-toolkit-backend-production.up.railway.app"

# Admin user details
admin_user = {
    "email": "admin@nextbelt.com",
    "password": "Admin123!",
    "full_name": "NextBelt Admin",
    "role": "admin"
}

# Create user
response = requests.post(f"{BACKEND_URL}/register", json=admin_user)

if response.status_code == 200:
    print("✅ Admin user created successfully!")
    print(f"Email: {admin_user['email']}")
    print(f"Password: {admin_user['password']}")
    print("\nYou can now log in at:")
    print("https://rmi-audit-toolkit-frontend-production.up.railway.app")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.json())
