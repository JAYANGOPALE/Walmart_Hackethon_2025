#!/usr/bin/env python3
"""
Database migration script for Walmart Employee Trust Score application.

This script helps migrate from the old database schema to the new enhanced schema
with improved security features and additional fields.
"""

import os
import sys
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_refactored import app, db
from models import User, LoginAttempt, SecurityEvent

def backup_old_database():
    """Create a backup of the old database."""
    import shutil
    
    old_db_path = "instance/walmart.db"
    backup_path = f"instance/walmart_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    if os.path.exists(old_db_path):
        print(f"📦 Creating backup: {backup_path}")
        shutil.copy2(old_db_path, backup_path)
        return backup_path
    else:
        print("⚠️  No existing database found to backup.")
        return None

def migrate_users():
    """Migrate user data to new schema."""
    print("👥 Migrating users...")
    
    # Check if we need to migrate from old schema
    try:
        # Try to access old password field
        old_users = db.session.execute("SELECT id, username, password, email, is_admin FROM user").fetchall()
        
        for old_user in old_users:
            user_id, username, old_password, email, is_admin = old_user
            
            # Check if user already exists in new schema
            existing_user = User.query.get(user_id)
            if existing_user:
                print(f"  ✅ User {username} already migrated")
                continue
            
            # Create new user with hashed password
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(old_password),
                is_admin=bool(is_admin)
            )
            new_user.id = user_id  # Preserve original ID
            new_user.created_at = datetime.now(timezone.utc)
            
            db.session.add(new_user)
            print(f"  🔄 Migrated user: {username}")
        
        db.session.commit()
        print("✅ User migration completed")
        
    except Exception as e:
        print(f"⚠️  User migration skipped (may be new installation): {e}")

def migrate_login_attempts():
    """Migrate login attempt data to new schema."""
    print("📊 Migrating login attempts...")
    
    try:
        # Try to access old login_attempts table
        old_attempts = db.session.execute("""
            SELECT id, user_id, timestamp, ip_address, location, latitude, longitude, trust_score, is_suspicious 
            FROM login_attempt
        """).fetchall()
        
        for old_attempt in old_attempts:
            attempt_id, user_id, timestamp, ip_address, location, latitude, longitude, trust_score, is_suspicious = old_attempt
            
            # Check if attempt already exists in new schema
            existing_attempt = LoginAttempt.query.get(attempt_id)
            if existing_attempt:
                print(f"  ✅ Login attempt {attempt_id} already migrated")
                continue
            
            # Create new login attempt
            new_attempt = LoginAttempt(
                user_id=user_id,
                ip_address=ip_address or '127.0.0.1',
                trust_score=trust_score or 0.0
            )
            new_attempt.id = attempt_id  # Preserve original ID
            new_attempt.timestamp = timestamp or datetime.now(timezone.utc)
            new_attempt.location = location
            new_attempt.latitude = latitude
            new_attempt.longitude = longitude
            new_attempt.is_suspicious = bool(is_suspicious)
            new_attempt.is_successful = True  # Assume successful for existing records
            new_attempt.auth_method = 'password'
            
            db.session.add(new_attempt)
            print(f"  🔄 Migrated login attempt: {attempt_id}")
        
        db.session.commit()
        print("✅ Login attempts migration completed")
        
    except Exception as e:
        print(f"⚠️  Login attempts migration skipped (may be new installation): {e}")

def create_admin_user():
    """Create a default admin user if none exists."""
    print("👑 Creating admin user...")
    
    admin_user = User.query.filter_by(is_admin=True).first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@walmart.com',
            password='admin123',  # Change this in production!
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created: admin/admin123")
        print("⚠️  IMPORTANT: Change admin password in production!")
    else:
        print("✅ Admin user already exists")

def create_sample_data():
    """Create sample data for testing."""
    print("📝 Creating sample data...")
    
    # Create sample employee users
    sample_users = [
        {'username': 'john_doe', 'email': 'john.doe@walmart.com', 'password': 'password123'},
        {'username': 'jane_smith', 'email': 'jane.smith@walmart.com', 'password': 'password123'},
        {'username': 'bob_wilson', 'email': 'bob.wilson@walmart.com', 'password': 'password123'},
    ]
    
    for user_data in sample_users:
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if not existing_user:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                is_admin=False
            )
            db.session.add(user)
            print(f"  ✅ Created sample user: {user_data['username']}")
    
    db.session.commit()
    print("✅ Sample data created")

def main():
    """Main migration function."""
    print("🔄 Walmart Employee Trust Score - Database Migration")
    print("=" * 60)
    
    with app.app_context():
        # Create backup
        backup_path = backup_old_database()
        
        # Create new tables
        print("\n🗄️  Creating new database schema...")
        db.create_all()
        print("✅ Database schema created")
        
        # Migrate existing data
        print("\n🔄 Migrating existing data...")
        migrate_users()
        migrate_login_attempts()
        
        # Create admin user
        print("\n👑 Setting up admin user...")
        create_admin_user()
        
        # Create sample data (optional)
        print("\n📝 Setting up sample data...")
        create_sample_data()
        
        print("\n" + "="*60)
        print("🎉 MIGRATION COMPLETED!")
        print("="*60)
        
        if backup_path:
            print(f"📦 Backup created: {backup_path}")
        
        print("\n📋 Next Steps:")
        print("1. Update your environment variables")
        print("2. Configure email service credentials")
        print("3. Change the admin password")
        print("4. Test the application")
        print("5. Deploy to production")
        
        print("\n🚀 You can now run: python app_refactored.py")

if __name__ == "__main__":
    main() 