#!/usr/bin/env python
"""
Create Django superuser programmatically
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import CustomUser

def create_admin():
    """Create admin user if it doesn't exist"""
    try:
        # Check if admin already exists
        admin_email = 'admin@farm2market.com'
        
        if CustomUser.objects.filter(email=admin_email).exists():
            print(f"Admin user with email {admin_email} already exists!")
            admin_user = CustomUser.objects.get(email=admin_email)
        else:
            # Create admin user
            admin_user = CustomUser.objects.create_user(
                username='admin',
                email=admin_email,
                password='admin123',
                first_name='Farm2Market',
                last_name='Admin',
                user_type='Admin',
                is_staff=True,
                is_superuser=True,
                is_approved=True
            )
            print("Admin user created successfully!")
        
        print("\n" + "="*50)
        print("DJANGO ADMIN CREDENTIALS")
        print("="*50)
        print(f"URL: http://localhost:8000/admin/")
        print(f"Email: {admin_email}")
        print(f"Username: admin")
        print(f"Password: admin123")
        print("="*50)
        
        return admin_user
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return None

if __name__ == '__main__':
    create_admin()
