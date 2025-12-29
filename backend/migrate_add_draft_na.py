"""
Database Migration: Add is_draft and is_na columns to question_responses
Run this once to update your existing database schema
"""
import sqlite3
import os

def migrate_database():
    db_path = "rmi_audit.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(question_responses)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_draft' in columns and 'is_na' in columns:
            print("✅ Columns already exist. No migration needed.")
            return
        
        # Add is_draft column if it doesn't exist
        if 'is_draft' not in columns:
            print("Adding is_draft column...")
            cursor.execute("""
                ALTER TABLE question_responses 
                ADD COLUMN is_draft BOOLEAN DEFAULT 0
            """)
            print("✅ Added is_draft column")
        
        # Add is_na column if it doesn't exist
        if 'is_na' not in columns:
            print("Adding is_na column...")
            cursor.execute("""
                ALTER TABLE question_responses 
                ADD COLUMN is_na BOOLEAN DEFAULT 0
            """)
            print("✅ Added is_na column")
        
        # Set existing responses to is_draft=0 and is_na=0
        cursor.execute("""
            UPDATE question_responses 
            SET is_draft = 0, is_na = 0 
            WHERE is_draft IS NULL OR is_na IS NULL
        """)
        
        conn.commit()
        print(f"✅ Migration completed successfully!")
        print(f"   Updated {cursor.rowcount} existing responses")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 Running database migration...")
    migrate_database()
