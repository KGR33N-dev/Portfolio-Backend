"""
Script to create the first admin user for the application
Run this after setting up the database to create an admin account
"""

import sys
import os
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal
from app.models import User, Base

# Create password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user(auto_create=False, username=None, email=None, password=None, full_name=None):
    """Create the first admin user"""
    
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.is_admin == True).first()
        
        if admin_user:
            print(f"Admin user already exists: {admin_user.username} ({admin_user.email})")
            return admin_user
        
        # Get admin details
        print("Creating first admin user...")
        
        if auto_create and username and email and password:
            # Use provided credentials for automated deployment
            print(f"Using provided credentials for user: {username}")
        else:
            # Interactive mode
            username = input("Enter admin username: ").strip()
            email = input("Enter admin email: ").strip()
            password = input("Enter admin password: ").strip()
            full_name = input("Enter full name (optional): ").strip() or None
        
        # Validate input
        if not username or not email or not password:
            print("Username, email, and password are required!")
            return None
        
        # Check if user with same username or email exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print("User with this username or email already exists!")
            return existing_user
        
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"User ID: {admin_user.id}")
        print("\nYou can now login to the admin panel with these credentials.")
        
        return admin_user
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def main():
    """Main function for script execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create admin user for Portfolio Backend')
    parser.add_argument('--auto', action='store_true', help='Auto-create using environment variables')
    parser.add_argument('--username', help='Admin username')
    parser.add_argument('--email', help='Admin email')
    parser.add_argument('--password', help='Admin password')
    parser.add_argument('--full-name', help='Admin full name')
    
    args = parser.parse_args()
    
    if args.auto:
        # Get credentials from environment variables
        username = args.username or os.getenv('ADMIN_USERNAME', 'admin')
        email = args.email or os.getenv('ADMIN_EMAIL', 'admin@kgr33n.com')
        password = args.password or os.getenv('ADMIN_PASSWORD')
        full_name = args.full_name or os.getenv('ADMIN_FULL_NAME', 'KGR33N Admin')
        
        if not password:
            print("❌ ADMIN_PASSWORD environment variable is required for auto-creation!")
            sys.exit(1)
        
        user = create_admin_user(
            auto_create=True,
            username=username,
            email=email,
            password=password,
            full_name=full_name
        )
        
        if user:
            print(f"🎉 Auto-created admin user: {user.username}")
        else:
            print("❌ Failed to create admin user")
            sys.exit(1)
    else:
        # Interactive mode
        create_admin_user()

if __name__ == "__main__":
    main()
