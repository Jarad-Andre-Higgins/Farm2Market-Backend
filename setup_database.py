#!/usr/bin/env python
"""
Setup script for Farm2Market database
This script will:
1. Create database migrations
2. Apply migrations
3. Create a superuser
4. Create sample data for testing
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from coreF2M.models import Category, FarmerProfile, BuyerProfile

User = get_user_model()

def setup_database():
    """Setup the database with initial data"""
    print("🚀 Setting up Farm2Market database...")
    
    # 1. Create migrations
    print("\n📝 Creating migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    # 2. Apply migrations
    print("\n🔄 Applying migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # 3. Create superuser
    print("\n👑 Creating superuser...")
    create_superuser()
    
    # 4. Create sample categories
    print("\n📂 Creating sample categories...")
    create_sample_categories()
    
    # 5. Create sample admin user
    print("\n👨‍💼 Creating admin user...")
    create_admin_user()
    
    print("\n✅ Database setup complete!")
    print("\n🎯 Next steps:")
    print("1. Run: python manage.py runserver")
    print("2. Access admin at: http://localhost:8000/admin/")
    print("3. Login with superuser credentials")
    print("4. Test farmer registration and approval process")

def create_superuser():
    """Create a superuser for Django admin"""
    if User.objects.filter(is_superuser=True).exists():
        print("   ✓ Superuser already exists")
        return
    
    try:
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@farm2market.com',
            password='admin123',
            user_type='Admin',
            first_name='Super',
            last_name='Admin',
            is_approved=True
        )
        print(f"   ✓ Superuser created: {superuser.username}")
        print(f"   📧 Email: {superuser.email}")
        print(f"   🔑 Password: admin123")
    except Exception as e:
        print(f"   ❌ Error creating superuser: {e}")

def create_admin_user():
    """Create a regular admin user"""
    if User.objects.filter(username='farmadmin').exists():
        print("   ✓ Admin user already exists")
        return
    
    try:
        admin_user = User.objects.create_user(
            username='farmadmin',
            email='farmadmin@farm2market.com',
            password='farmadmin123',
            user_type='Admin',
            first_name='Farm',
            last_name='Administrator',
            is_approved=True,
            is_staff=True
        )
        print(f"   ✓ Admin user created: {admin_user.username}")
        print(f"   📧 Email: {admin_user.email}")
        print(f"   🔑 Password: farmadmin123")
    except Exception as e:
        print(f"   ❌ Error creating admin user: {e}")

def create_sample_categories():
    """Create sample product categories"""
    categories = [
        'Vegetables',
        'Fruits',
        'Grains & Cereals',
        'Tubers & Roots',
        'Herbs & Spices',
        'Legumes',
        'Dairy Products',
        'Poultry & Eggs'
    ]
    
    created_count = 0
    for category_name in categories:
        category, created = Category.objects.get_or_create(name=category_name)
        if created:
            created_count += 1
    
    print(f"   ✓ Created {created_count} new categories")
    print(f"   📊 Total categories: {Category.objects.count()}")

def create_sample_farmer():
    """Create a sample farmer for testing"""
    if User.objects.filter(username='testfarmer').exists():
        print("   ✓ Test farmer already exists")
        return
    
    try:
        farmer = User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='farmer123',
            user_type='Farmer',
            first_name='John',
            last_name='Farmer',
            phone_number='+237 6XX XXX XXX',
            is_approved=False  # Needs admin approval
        )
        
        # Create farmer profile
        FarmerProfile.objects.create(
            farmer=farmer,
            location='Douala, Cameroon'
        )
        
        print(f"   ✓ Test farmer created: {farmer.username}")
        print(f"   📧 Email: {farmer.email}")
        print(f"   🔑 Password: farmer123")
        print(f"   ⏳ Status: Pending approval")
    except Exception as e:
        print(f"   ❌ Error creating test farmer: {e}")

def create_sample_buyer():
    """Create a sample buyer for testing"""
    if User.objects.filter(username='testbuyer').exists():
        print("   ✓ Test buyer already exists")
        return
    
    try:
        buyer = User.objects.create_user(
            username='testbuyer',
            email='buyer@test.com',
            password='buyer123',
            user_type='Buyer',
            first_name='Jane',
            last_name='Buyer',
            phone_number='+237 6YY YYY YYY',
            is_approved=True  # Auto-approved
        )
        
        # Create buyer profile
        BuyerProfile.objects.create(
            buyer=buyer,
            location='Yaounde, Cameroon'
        )
        
        print(f"   ✓ Test buyer created: {buyer.username}")
        print(f"   📧 Email: {buyer.email}")
        print(f"   🔑 Password: buyer123")
    except Exception as e:
        print(f"   ❌ Error creating test buyer: {e}")

if __name__ == '__main__':
    setup_database()
    
    # Also create sample users
    print("\n👥 Creating sample users for testing...")
    create_sample_farmer()
    create_sample_buyer()
    
    print("\n🎉 Setup complete! You can now:")
    print("1. Start the server: python manage.py runserver")
    print("2. Access admin: http://localhost:8000/admin/")
    print("3. Test farmer registration at: http://localhost:8000/farmer dashboard.html")
    print("4. Approve farmers in the admin panel")
