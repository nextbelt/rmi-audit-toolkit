import sqlite3

conn = sqlite3.connect('rmi_audit.db')

print("=== RESPONSE ANALYSIS ===\n")

# Check all responses
results = conn.execute('''
    SELECT qr.id, qr.question_id, qr.response_value, qr.numeric_score, 
           qr.is_draft, qb.question_code, qb.question_type
    FROM question_responses qr 
    JOIN question_bank qb ON qr.question_id = qb.id 
    WHERE qr.is_draft = 0
    ORDER BY qb.question_code
    LIMIT 20
''').fetchall()

print(f"Found {len(results)} non-draft responses:\n")
for resp_id, qid, value, score, draft, code, qtype in results:
    score_display = f"{score}" if score is not None else "NULL"
    print(f"{code} (Type: {qtype})")
    print(f"  Value: {value[:50] if value else 'NULL'}")
    print(f"  Numeric Score: {score_display}")
    print()

# Count by score status
null_count = conn.execute('SELECT COUNT(*) FROM question_responses WHERE numeric_score IS NULL AND is_draft = 0').fetchone()[0]
with_score = conn.execute('SELECT COUNT(*) FROM question_responses WHERE numeric_score IS NOT NULL AND is_draft = 0').fetchone()[0]

print(f"\n=== SUMMARY ===")
print(f"Responses with NULL numeric_score: {null_count}")
print(f"Responses with numeric_score: {with_score}")

conn.close()
