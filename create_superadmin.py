#!/usr/bin/env python
"""
Create superadmin for Agriport
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import CustomUser
from django.contrib.auth import authenticate

def create_superadmin():
    """Create superadmin user"""
    try:
        # Check if superadmin exists
        if CustomUser.objects.filter(email='admin@agriport.com').exists():
            print("✅ Superadmin already exists")
            admin = CustomUser.objects.get(email='admin@agriport.com')
            print(f"   Username: {admin.username}")
            print(f"   Email: {admin.email}")
            print(f"   Active: {admin.is_active}")
            print(f"   Superuser: {admin.is_superuser}")
            print(f"   User Type: {admin.user_type}")
        else:
            # Create superadmin
            superadmin = CustomUser.objects.create_user(
                username='superadmin',
                email='admin@agriport.com',
                password='admin123',
                first_name='Super',
                last_name='Admin',
                user_type='Admin',
                is_approved=True,
                is_active=True,
                is_staff=True,
                is_superuser=True
            )
            print(f"✅ Created superadmin: {superadmin.email}")
        
        # Test authentication
        print("\n🔐 Testing authentication...")
        user = authenticate(username='admin@agriport.com', password='admin123')
        if user:
            print(f"✅ Authentication successful!")
            print(f"   User: {user.username}")
            print(f"   Type: {user.user_type}")
            print(f"   Active: {user.is_active}")
        else:
            print("❌ Authentication failed!")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    create_superadmin()
