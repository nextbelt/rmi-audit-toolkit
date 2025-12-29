import sqlite3

conn = sqlite3.connect('rmi_audit.db')
cursor = conn.cursor()

print("=== PILLAR SCORES ===")
scores = cursor.execute('SELECT pillar, final_score FROM scores WHERE pillar IS NOT NULL').fetchall()
for pillar, score in scores:
    print(f"{pillar}: {score}")

print("\n=== TECHNOLOGY RESPONSES ===")
tech_responses = cursor.execute('''
    SELECT qb.question_code, qb.question_text, qr.numeric_score, qb.is_critical
    FROM question_responses qr 
    JOIN question_bank qb ON qr.question_id = qb.id 
    WHERE qb.pillar LIKE '%TECH%' AND qr.is_draft = 0
''').fetchall()

print(f"Found {len(tech_responses)} Technology responses:")
for code, text, score, critical in tech_responses:
    crit_flag = " [CRITICAL]" if critical else ""
    print(f"  {code}: {score}{crit_flag} - {text[:50]}")

print("\n=== OBSERVATIONS ===")
obs_count = cursor.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
print(f"Total observations: {obs_count}")

if obs_count > 0:
    obs = cursor.execute('SELECT title, pillar, pass_fail_result FROM observations LIMIT 5').fetchall()
    for title, pillar, pass_fail in obs:
        print(f"  {title} ({pillar}): {'PASS' if pass_fail else 'FAIL'}")

conn.close()
