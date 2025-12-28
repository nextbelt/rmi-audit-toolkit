"""Create a local user by directly inserting into SQLite database with a pre-hashed password."""
import sqlite3
from datetime import datetime

# Connect to the local SQLite database
conn = sqlite3.connect('rmi_audit.db')
cursor = conn.cursor()

# Pre-hashed password for "admin123" using bcrypt
# This was generated with: bcrypt.hashpw(b"admin123", bcrypt.gensalt())
hashed_password = "$2b$12$LQCnXGj5YvGmvH7fYdR8HOoN3qK7KGR6sVH.FcC5BZPvJQF1TlBEO"

# Insert admin user
cursor.execute("""
    INSERT INTO users (email, hashed_password, full_name, role, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
""", (
    'admin@local.com',
    hashed_password,
    'Local Admin',
    'admin',
    1,
    datetime.utcnow().isoformat()
))

conn.commit()
conn.close()

print("✅ Local admin user created!")
print("Email: admin@local.com")
print("Password: admin123")
