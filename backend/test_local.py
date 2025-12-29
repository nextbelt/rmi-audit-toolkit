import requests

# Test local backend
url = "http://localhost:8000"

# Test login
print("Testing login...")
response = requests.post(f"{url}/token", data={
    "username": "admin@local.com",
    "password": "admin123"
})
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"\n✅ Login successful! Token: {token[:20]}...")
    
    # Test getting questions
    print("\nTesting /questions endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    q_response = requests.get(f"{url}/questions", headers=headers)
    print(f"Status: {q_response.status_code}")
    print(f"Response: {q_response.text[:500]}")
