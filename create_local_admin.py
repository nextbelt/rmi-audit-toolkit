"""
Create local admin user for development
"""
import requests

# Local backend
BACKEND_URL = "http://localhost:8001"

admin_user = {
    "email": "nextbelt@next-belt.com",
    "password": "C/aljan2026*",
    "full_name": "NextBelt Admin",
    "role": "admin"
}

print("Creating local admin user...")
print(f"Email: {admin_user['email']}")

try:
    response = requests.post(f"{BACKEND_URL}/register", json=admin_user)
    
    if response.status_code == 200:
        print("✅ Local admin user created!")
        print("\nYou can now log in at http://localhost:3000")
        print(f"Email: {admin_user['email']}")
        print(f"Password: {admin_user['password']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure the backend is running on http://localhost:8000")
