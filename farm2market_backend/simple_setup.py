#!/usr/bin/env python
"""
Simple setup script that runs from the correct directory
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Main setup function"""
    print("🚀 Simple Farm2Market Setup")
    print("=" * 40)
    
    # Set the settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
    
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path}")
    
    try:
        print("\n1️⃣ Setting up Django...")
        django.setup()
        print("✅ Django setup successful")
        
        print("\n2️⃣ Creating migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        print("\n3️⃣ Applying migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("\n4️⃣ Creating superuser...")
        create_superuser()
        
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Run: python manage.py runserver")
        print("2. Access: http://localhost:8000/admin/")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def create_superuser():
    """Create superuser if it doesn't exist"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(is_superuser=True).exists():
            print("   ✓ Superuser already exists")
            return
        
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@farm2market.com',
            password='admin123',
            user_type='Admin',
            is_approved=True
        )
        print(f"   ✅ Superuser created: {superuser.username}")
        print(f"   📧 Email: admin@farm2market.com")
        print(f"   🔑 Password: admin123")
        
    except Exception as e:
        print(f"   ❌ Error creating superuser: {e}")

if __name__ == '__main__':
    main()
