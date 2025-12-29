"""Test submitting a response to the production API"""
import requests
import os
import sys

API_URL = os.getenv("API_URL", "http://localhost:8000")
EMAIL = os.getenv("ADMIN_EMAIL")
PASSWORD = os.getenv("ADMIN_PASSWORD")

if not EMAIL or not PASSWORD:
    print("❌ ERROR: Set ADMIN_EMAIL and ADMIN_PASSWORD environment variables")
    sys.exit(1)

# Login
print("Logging in...")
r = requests.post(f"{API_URL}/token", data={"username": EMAIL, "password": PASSWORD})
token = r.json()["access_token"]
print("✅ Logged in\n")

headers = {"Authorization": f"Bearer {token}"}

# Get questions
print("Fetching questions...")
q = requests.get(f"{API_URL}/questions", headers=headers)
questions = q.json()
print(f"✅ Found {len(questions)} questions\n")

if questions:
    first_question = questions[0]
    print(f"Testing with question: {first_question['question_code']}")
    print(f"Question text: {first_question['question_text'][:50]}...\n")
    
    # Try to submit a response
    print("Submitting test response...")
    payload = {
        "question_id": first_question["id"],
        "response_value": "3",  # Test likert score
        "evidence_notes": "Test response"
    }
    
    print(f"Payload: {payload}")
    
    response = requests.post(
        f"{API_URL}/assessments/1/responses",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
