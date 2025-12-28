"""
Database Initialization Script
Run this to set up the database and seed the question bank
"""
from database import init_db, SessionLocal
from question_bank import seed_question_bank
from models import User
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def initialize_database():
    """Initialize database with tables and seed data"""
    print("🔧 Initializing database...")
    
    # Create tables
    init_db()
    print("✅ Database tables created")
    
    # Seed question bank
    db = SessionLocal()
    try:
        print("🔧 Seeding question bank...")
        count = seed_question_bank(db)
        print(f"✅ Seeded {count} questions")
        
        # Create default admin user
        print("🔧 Creating default admin user...")
        admin_exists = db.query(User).filter(User.email == "admin@nextbelt.com").first()
        
        if not admin_exists:
            admin_user = User(
                email="admin@nextbelt.com",
                hashed_password=pwd_context.hash("admin123"),  # Change in production!
                full_name="System Administrator",
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Admin user created (email: admin@nextbelt.com, password: admin123)")
        else:
            print("ℹ️  Admin user already exists")
        
    finally:
        db.close()
    
    print("\n✅ Database initialization complete!")
    print("\n📊 Next steps:")
    print("1. Run the API server: python main.py")
    print("2. Access API docs: http://localhost:8000/docs")
    print("3. Login with: admin@nextbelt.com / admin123")


if __name__ == "__main__":
    initialize_database()
