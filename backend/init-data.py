#!/usr/bin/env python3
"""
Skrypt do inicjalizacji danych po uruchomieniu migracji
Teraz używa create_admin.py do kompleksowej inicjalizacji
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Create admin user - database should already be initialized by startup"""
    print("👑 Tworzenie administratora...")
    
    try:
        # Import create_admin module
        from app.create_admin import create_admin_user
        
        print("🏗️  Tworzę konto administratora...")
        
        # Get admin credentials from environment or use defaults
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@email.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')  # Default password for development
        admin_full_name = os.getenv('ADMIN_FULL_NAME', 'Administrator')
        
        # Create admin user (database should already be initialized by FastAPI startup)
        admin_user = create_admin_user(
            auto_create=False,  # Don't auto-init data, it's already done by startup
            username=admin_username,
            email=admin_email,
            password=admin_password,
            full_name=admin_full_name
        )
        
        if admin_user:
            print("✅ Administrator utworzony pomyślnie!")
            print(f"📧 Email: {admin_email}")
            print(f"👤 Username: {admin_username}")
            print(f"🔑 Password: {admin_password}")
        else:
            print("⚠️  Administrator już istnieje lub wystąpił problem")
        
    except Exception as e:
        print(f"❌ Błąd podczas inicjalizacji: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
