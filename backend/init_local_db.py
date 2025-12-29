"""Initialize local database with admin user and questions"""
import sqlite3
import json

# Connect to SQLite database
conn = sqlite3.connect('rmi_audit.db')
cursor = conn.cursor()

# Create admin user (password: admin123)
try:
    cursor.execute("""
        INSERT INTO users (email, full_name, hashed_password, role, is_active)
        VALUES ('admin@local.com', 'Local Admin', 'local_dev_hash', 'admin', 1)
    """)
    print("✅ Created admin user (admin@local.com / admin123)")
except sqlite3.IntegrityError:
    print("ℹ️  Admin user already exists")

# Seed questions
questions = [
    ("P-01", "PEOPLE", "likert", "Does the organization have documented competency requirements for reliability roles?", "MANAGER", "Competency", 0, 5),
    ("P-02", "PEOPLE", "likert", "Are there structured training programs for maintenance and operations personnel?", "TECHNICIAN", "Training", 0, 5),
    ("P-03", "PEOPLE", "likert", "How often are reliability KPIs reviewed with the team?", "MANAGER", "Performance Management", 0, 5),
    ("P-04", "PEOPLE", "observational", "Observe: Are safety and reliability procedures clearly posted and accessible?", "AUDITOR", "Safety Culture", 0, 5),
    ("P-05", "PEOPLE", "likert", "Is there a formal knowledge transfer process when experienced personnel leave?", "MANAGER", "Knowledge Management", 1, 5),
    ("PR-01", "PROCESS", "likert", "Are work orders prioritized using risk-based criteria?", "PLANNER", "Planning", 0, 5),
    ("PR-02", "PROCESS", "data_input", "What is the percentage of planned vs. reactive maintenance work?", "AUDITOR", "Maintenance Strategy", 1, 5),
    ("PR-03", "PROCESS", "likert", "How are Root Cause Analysis findings implemented into preventive measures?", "MANAGER", "Continuous Improvement", 1, 5),
    ("PR-04", "PROCESS", "observational", "Observe: Are procedures followed consistently during maintenance activities?", "AUDITOR", "Process Adherence", 0, 5),
    ("PR-05", "PROCESS", "data_input", "Review CMMS data: What is the PM compliance rate over the last 12 months?", "AUDITOR", "PM Execution", 1, 5),
    ("T-01", "TECHNOLOGY", "binary", "Is a CMMS system actively used for work order management?", "PLANNER", "CMMS", 1, 5),
    ("T-02", "TECHNOLOGY", "data_input", "What percentage of critical assets have condition monitoring in place?", "AUDITOR", "Condition Monitoring", 1, 5),
    ("T-03", "TECHNOLOGY", "binary", "Are predictive maintenance technologies (vibration, thermography, oil analysis) utilized?", "MANAGER", "Predictive Maintenance", 0, 5),
    ("T-04", "TECHNOLOGY", "observational", "Observe: Are calibration stickers current on test equipment?", "AUDITOR", "Instrumentation", 0, 5),
    ("T-05", "TECHNOLOGY", "data_input", "Review asset criticality rankings: Are critical assets clearly identified in CMMS?", "AUDITOR", "Asset Management", 1, 5),
    ("T-06", "TECHNOLOGY", "binary", "Is there integration between CMMS and other business systems (ERP, procurement)?", "MANAGER", "System Integration", 0, 5),
]

added = 0
for q in questions:
    try:
        cursor.execute("""
            INSERT INTO question_bank 
            (question_code, pillar, question_type, question_text, target_role, subcategory, is_critical, max_score, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, q)
        added += 1
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()

print(f"✅ Added {added} questions to database")
print(f"\n{'='*60}")
print("Local database ready!")
print("Login: admin@local.com / admin123")
print(f"{'='*60}")
