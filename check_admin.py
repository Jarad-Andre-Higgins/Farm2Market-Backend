#!/usr/bin/env python
"""
Check admin credentials for testing
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import CustomUser

def check_admin_credentials():
    print("🔍 Checking admin credentials...")
    
    # Check for existing admin users
    admins = CustomUser.objects.filter(user_type='Admin')
    
    if admins.exists():
        for admin in admins:
            print(f"\n✅ Found admin: {admin.email}")
            print(f"   Username: {admin.username}")
            print(f"   Active: {admin.is_active}")
            print(f"   Superuser: {admin.is_superuser}")
            print(f"   Password 'admin123' works: {admin.check_password('admin123')}")
    else:
        print("❌ No admin users found. Creating one...")
        
        # Create admin user
        try:
            admin = CustomUser.objects.create_user(
                email='admin@agriport.com',
                username='agriportadmin',
                password='admin123',
                first_name='Agriport',
                last_name='Admin',
                user_type='Admin',
                is_active=True,
                is_approved=True,
                is_staff=True,
                is_superuser=True
            )
            print(f"✅ Created admin: {admin.email}")
            print(f"   Password: admin123")
        except Exception as e:
            print(f"❌ Error creating admin: {e}")
    
    print("\n🔑 Admin Login Credentials:")
    admin = CustomUser.objects.filter(user_type='Admin').first()
    if admin:
        print(f"   Email: {admin.email}")
        print(f"   Password: admin123")
        print(f"   Status: {'✅ Ready' if admin.is_active else '❌ Inactive'}")
    
    # Check pending farmers
    pending_farmers = CustomUser.objects.filter(user_type='Farmer', is_approved=False)
    print(f"\n📋 Pending farmer approvals: {pending_farmers.count()}")
    
    for farmer in pending_farmers:
        print(f"   - {farmer.email} ({farmer.first_name} {farmer.last_name})")

if __name__ == '__main__':
    check_admin_credentials()
