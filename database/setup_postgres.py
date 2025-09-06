#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script for Population Density Analyzer
Run this script once to set up the database and create the initial admin user.
"""

import warnings
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import hashlib
from database_config import DATABASE_URL

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_database():
    """Set up the PostgreSQL database"""
    print("🔧 Setting up PostgreSQL database...")

    try:
        # Create engine and connect
        engine = create_engine(DATABASE_URL)
        print("✅ Connected to PostgreSQL database")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Created database tables")

        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Create default admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                password_hash=hash_password("admin123"),
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Created default admin user (admin/admin123)")
        else:
            print("ℹ️  Admin user already exists")

        db.close()
        print("🎉 Database setup completed successfully!")
        print("\n📋 Default Credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Role: Administrator")

    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        print("\n🔍 Troubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL environment variable")
        print("3. Verify database credentials are correct")
        print("4. Ensure the database exists: createdb population_db")
        return False

    return True

if __name__ == "__main__":
    print("🚀 Population Density Analyzer - Database Setup")
    print("=" * 50)

    if setup_database():
        print("\n✅ Setup complete! You can now run the Streamlit app.")
        print("   Run: streamlit run 'population density.py'")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
