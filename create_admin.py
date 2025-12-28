"""
Simple script to create an admin user via the backend API
Run this to create your first admin user in the backend database
"""
import requests

# Backend URL
BACKEND_URL = "https://rmi-audit-toolkit-backend-production.up.railway.app"

# Admin user details - CHANGE THESE TO MATCH YOUR SUPABASE USER
admin_user = {
    "email": "nextbelt@next-belt.com",  # Must match Supabase email
    "password": "C/aljan2026*",         # Can be any password (backend stores separately)
    "full_name": "NextBelt Admin",
    "role": "admin"
}

print("Creating admin user in backend database...")
print(f"Email: {admin_user['email']}")
print(f"Role: {admin_user['role']}")
print()

# Create user
try:
    response = requests.post(f"{BACKEND_URL}/register", json=admin_user)
    
    if response.status_code == 200:
        print("✅ Admin user created successfully in backend database!")
        print()
        print("You can now log in at:")
        print("https://rmi-audit-toolkit-frontend-production.up.railway.app")
        print()
        print("Use your Supabase credentials:")
        print(f"Email: {admin_user['email']}")
        print("Password: [your Supabase password]")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
except Exception as e:
    print(f"❌ Error connecting to backend: {e}")
    print()
    print("Make sure the backend is deployed and accessible at:")
    print(BACKEND_URL)

