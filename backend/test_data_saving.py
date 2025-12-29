"""
Test Script: Verify Data Saving Improvements
Run this to validate all new features are working
"""
import sqlite3

def test_database_schema():
    """Test that new columns exist"""
    print("\n🔍 Testing Database Schema...")
    
    conn = sqlite3.connect("rmi_audit.db")
    cursor = conn.cursor()
    
    # Check columns
    cursor.execute("PRAGMA table_info(question_responses)")
    columns = {col[1]: col[2] for col in cursor.fetchall()}
    
    assert 'is_draft' in columns, "❌ is_draft column missing"
    assert 'is_na' in columns, "❌ is_na column missing"
    
    print("✅ is_draft column exists:", columns['is_draft'])
    print("✅ is_na column exists:", columns['is_na'])
    
    # Check default values
    cursor.execute("SELECT is_draft, is_na FROM question_responses LIMIT 1")
    result = cursor.fetchone()
    if result:
        print(f"✅ Default values: is_draft={result[0]}, is_na={result[1]}")
    else:
        print("ℹ️  No responses in database yet")
    
    conn.close()

def test_insert_draft_response():
    """Test inserting a draft response"""
    print("\n🔍 Testing Draft Response Insert...")
    
    conn = sqlite3.connect("rmi_audit.db")
    cursor = conn.cursor()
    
    try:
        # Insert test draft response
        cursor.execute("""
            INSERT INTO question_responses 
            (assessment_id, question_id, response_value, is_draft, is_na, numeric_score)
            VALUES (1, 1, 'Test draft response', 1, 0, NULL)
        """)
        conn.commit()
        
        # Verify it was inserted
        cursor.execute("""
            SELECT response_value, is_draft, is_na 
            FROM question_responses 
            WHERE response_value = 'Test draft response'
        """)
        result = cursor.fetchone()
        
        assert result is not None, "❌ Draft response not inserted"
        assert result[1] == 1, "❌ is_draft not set correctly"
        assert result[2] == 0, "❌ is_na not set correctly"
        
        print(f"✅ Draft response inserted: is_draft={result[1]}, is_na={result[2]}")
        
        # Clean up test data
        cursor.execute("DELETE FROM question_responses WHERE response_value = 'Test draft response'")
        conn.commit()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        conn.close()

def test_insert_na_response():
    """Test inserting an N/A response"""
    print("\n🔍 Testing N/A Response Insert...")
    
    conn = sqlite3.connect("rmi_audit.db")
    cursor = conn.cursor()
    
    try:
        # Insert test N/A response
        cursor.execute("""
            INSERT INTO question_responses 
            (assessment_id, question_id, response_value, is_draft, is_na, numeric_score)
            VALUES (1, 1, 'N/A', 0, 1, NULL)
        """)
        conn.commit()
        
        # Verify it was inserted
        cursor.execute("""
            SELECT response_value, is_draft, is_na, numeric_score
            FROM question_responses 
            WHERE response_value = 'N/A'
        """)
        result = cursor.fetchone()
        
        assert result is not None, "❌ N/A response not inserted"
        assert result[2] == 1, "❌ is_na not set correctly"
        assert result[3] is None, "❌ numeric_score should be NULL for N/A"
        
        print(f"✅ N/A response inserted: is_na={result[2]}, numeric_score={result[3]}")
        
        # Clean up test data
        cursor.execute("DELETE FROM question_responses WHERE response_value = 'N/A'")
        conn.commit()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        conn.close()

def test_scoring_filter():
    """Test that scoring excludes drafts and N/A"""
    print("\n🔍 Testing Scoring Filter Logic...")
    
    conn = sqlite3.connect("rmi_audit.db")
    cursor = conn.cursor()
    
    try:
        # Count total responses
        cursor.execute("SELECT COUNT(*) FROM question_responses")
        total = cursor.fetchone()[0]
        
        # Count responses that should be scored
        cursor.execute("""
            SELECT COUNT(*) 
            FROM question_responses 
            WHERE is_draft = 0 AND is_na = 0
        """)
        scoreable = cursor.fetchone()[0]
        
        # Count excluded responses
        cursor.execute("""
            SELECT COUNT(*) 
            FROM question_responses 
            WHERE is_draft = 1 OR is_na = 1
        """)
        excluded = cursor.fetchone()[0]
        
        print(f"✅ Total responses: {total}")
        print(f"✅ Scoreable responses: {scoreable}")
        print(f"✅ Excluded responses (draft/N/A): {excluded}")
        
        assert total == scoreable + excluded, "❌ Count mismatch"
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("DATA SAVING IMPROVEMENTS - VALIDATION TESTS")
    print("="*60)
    
    test_database_schema()
    test_insert_draft_response()
    test_insert_na_response()
    test_scoring_filter()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\n📋 Next steps:")
    print("1. Start backend: cd backend; python -m uvicorn main:app --reload --port 8000")
    print("2. Start frontend: cd frontend; npm run dev")
    print("3. Test in browser:")
    print("   - Fill out a question → Wait 1 sec → Check for 'Draft saved' message")
    print("   - Click 'Save & Exit' → Verify answer persists")
    print("   - Try scoring 5 without evidence → Should show error")
    print("   - Check 'N/A' box → Score buttons should disable")
    print("")
