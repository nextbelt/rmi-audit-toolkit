"""Seed the question bank with predefined RMI assessment questions."""
import requests
import sys

API_URL = "https://rmi-audit-toolkit-backend-production.up.railway.app"

# Login credentials
EMAIL = "nextbelt@next-belt.com"
PASSWORD = "C/aljan2026*"

# Predefined questions
QUESTIONS = [
    # PEOPLE Questions (P-01 to P-05)
    {"question_code": "P-01", "pillar": "people", "question_type": "likert", "question_text": "Does the organization have documented competency requirements for reliability roles?", "target_role": "manager", "subcategory": "Competency", "is_critical": False, "max_score": 5},
    {"question_code": "P-02", "pillar": "people", "question_type": "likert", "question_text": "Are there structured training programs for maintenance and operations personnel?", "target_role": "technician", "subcategory": "Training", "is_critical": False, "max_score": 5},
    {"question_code": "P-03", "pillar": "people", "question_type": "likert", "question_text": "How often are reliability KPIs reviewed with the team?", "target_role": "manager", "subcategory": "Performance Management", "is_critical": False, "max_score": 5},
    {"question_code": "P-04", "pillar": "people", "question_type": "observational", "question_text": "Observe: Are safety and reliability procedures clearly posted and accessible?", "target_role": "auditor", "subcategory": "Safety Culture", "is_critical": False, "max_score": 5},
    {"question_code": "P-05", "pillar": "people", "question_type": "likert", "question_text": "Is there a formal knowledge transfer process when experienced personnel leave?", "target_role": "manager", "subcategory": "Knowledge Management", "is_critical": True, "max_score": 5},
    
    # PROCESS Questions (PR-01 to PR-05)
    {"question_code": "PR-01", "pillar": "process", "question_type": "likert", "question_text": "Are work orders prioritized using risk-based criteria?", "target_role": "planner", "subcategory": "Planning", "is_critical": False, "max_score": 5},
    {"question_code": "PR-02", "pillar": "process", "question_type": "data_input", "question_text": "What is the percentage of planned vs. reactive maintenance work?", "target_role": "auditor", "subcategory": "Maintenance Strategy", "is_critical": True, "max_score": 5},
    {"question_code": "PR-03", "pillar": "process", "question_type": "likert", "question_text": "How are Root Cause Analysis findings implemented into preventive measures?", "target_role": "manager", "subcategory": "Continuous Improvement", "is_critical": True, "max_score": 5},
    {"question_code": "PR-04", "pillar": "process", "question_type": "observational", "question_text": "Observe: Are procedures followed consistently during maintenance activities?", "target_role": "auditor", "subcategory": "Process Adherence", "is_critical": False, "max_score": 5},
    {"question_code": "PR-05", "pillar": "process", "question_type": "data_input", "question_text": "Review CMMS data: What is the PM compliance rate over the last 12 months?", "target_role": "auditor", "subcategory": "PM Execution", "is_critical": True, "max_score": 5},
    
    # TECHNOLOGY Questions (T-01 to T-06)
    {"question_code": "T-01", "pillar": "technology", "question_type": "binary", "question_text": "Is a CMMS system actively used for work order management?", "target_role": "planner", "subcategory": "CMMS", "is_critical": True, "max_score": 5},
    {"question_code": "T-02", "pillar": "technology", "question_type": "data_input", "question_text": "What percentage of critical assets have condition monitoring in place?", "target_role": "auditor", "subcategory": "Condition Monitoring", "is_critical": True, "max_score": 5},
    {"question_code": "T-03", "pillar": "technology", "question_type": "binary", "question_text": "Are predictive maintenance technologies (vibration, thermography, oil analysis) utilized?", "target_role": "manager", "subcategory": "Predictive Maintenance", "is_critical": False, "max_score": 5},
    {"question_code": "T-04", "pillar": "technology", "question_type": "observational", "question_text": "Observe: Are calibration stickers current on test equipment?", "target_role": "auditor", "subcategory": "Instrumentation", "is_critical": False, "max_score": 5},
    {"question_code": "T-05", "pillar": "technology", "question_type": "data_input", "question_text": "Review asset criticality rankings: Are critical assets clearly identified in CMMS?", "target_role": "auditor", "subcategory": "Asset Management", "is_critical": True, "max_score": 5},
    {"question_code": "T-06", "pillar": "technology", "question_type": "binary", "question_text": "Is there integration between CMMS and other business systems (ERP, procurement)?", "target_role": "manager", "subcategory": "System Integration", "is_critical": False, "max_score": 5},
]

def main():
    # Login
    print("Logging in...")
    login_data = {
        "username": EMAIL,
        "password": PASSWORD
    }
    response = requests.post(f"{API_URL}/token", data=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        sys.exit(1)
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"✅ Logged in successfully\n")
    
    # Add questions
    added = 0
    for q in QUESTIONS:
        print(f"Adding {q['code']}: {q['question_text'][:60]}...")
        response = requests.post(f"{API_URL}/questions", json=q, headers=headers)
        
        if response.status_code in [200, 201]:
            added += 1
            print(f"  ✅ Added")
        else:
            print(f"  ⚠️  {response.status_code}: {response.text}")
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully added {added}/{len(QUESTIONS)} questions to the database")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
