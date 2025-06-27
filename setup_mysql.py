#!/usr/bin/env python
"""
MySQL Setup script for Farm2Market
This script will:
1. Check MySQL connection
2. Create database if it doesn't exist
3. Create migrations
4. Apply migrations
5. Create superuser and sample data
"""

import os
import sys
import django
import mysql.connector
from mysql.connector import Error

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')

def check_mysql_connection():
    """Check if MySQL is running and accessible"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Abdel@ictu2023',
            port=3306
        )
        if connection.is_connected():
            print("✅ MySQL connection successful")
            return connection
        else:
            print("❌ Failed to connect to MySQL")
            return None
    except Error as e:
        print(f"❌ MySQL connection error: {e}")
        return None

def create_database_if_not_exists():
    """Create the farmtomarket database if it doesn't exist"""
    connection = check_mysql_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Check if database exists
        cursor.execute("SHOW DATABASES LIKE 'farmtomarket'")
        result = cursor.fetchone()
        
        if result:
            print("✅ Database 'farmtomarket' already exists")
        else:
            # Create database
            cursor.execute("CREATE DATABASE farmtomarket CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database 'farmtomarket' created successfully")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Error creating database: {e}")
        return False

def setup_django():
    """Setup Django and run migrations"""
    try:
        # Setup Django
        django.setup()
        
        from django.core.management import execute_from_command_line
        from django.contrib.auth import get_user_model
        from coreF2M.models import Category, FarmerProfile, BuyerProfile, Notification
        
        User = get_user_model()
        
        print("\n📝 Creating Django migrations...")
        execute_from_command_line(['manage.py', 'makemigrations', 'coreF2M'])
        
        print("\n🔄 Applying migrations to MySQL...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("\n👑 Creating superuser...")
        create_superuser(User)
        
        print("\n👨‍💼 Creating admin user...")
        create_admin_user(User)
        
        print("\n📂 Creating sample categories...")
        create_sample_categories(Category)
        
        print("\n👥 Creating test users...")
        create_test_users(User, FarmerProfile, BuyerProfile)
        
        return True
        
    except Exception as e:
        print(f"❌ Django setup error: {e}")
        return False

def create_superuser(User):
    """Create Django superuser"""
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
        print(f"   ✅ Superuser created: {superuser.username}")
        print(f"   📧 Email: admin@farm2market.com")
        print(f"   🔑 Password: admin123")
    except Exception as e:
        print(f"   ❌ Error creating superuser: {e}")

def create_admin_user(User):
    """Create regular admin user"""
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
        print(f"   ✅ Admin user created: {admin_user.username}")
        print(f"   📧 Email: farmadmin@farm2market.com")
        print(f"   🔑 Password: farmadmin123")
    except Exception as e:
        print(f"   ❌ Error creating admin user: {e}")

def create_sample_categories(Category):
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
    
    print(f"   ✅ Created {created_count} new categories")
    print(f"   📊 Total categories: {Category.objects.count()}")

def create_test_users(User, FarmerProfile, BuyerProfile):
    """Create test farmer and buyer"""
    # Test Farmer
    if not User.objects.filter(username='testfarmer').exists():
        try:
            farmer = User.objects.create_user(
                username='testfarmer',
                email='farmer@test.com',
                password='farmer123',
                user_type='Farmer',
                first_name='John',
                last_name='TestFarmer',
                phone_number='+237 612 345 678',
                is_approved=False  # Needs approval
            )
            
            FarmerProfile.objects.create(
                farmer=farmer,
                location='Douala, Cameroon'
            )
            
            print(f"   ✅ Test farmer created: {farmer.username}")
            print(f"   📧 Email: farmer@test.com")
            print(f"   🔑 Password: farmer123")
            print(f"   ⏳ Status: Pending approval")
        except Exception as e:
            print(f"   ❌ Error creating test farmer: {e}")
    else:
        print("   ✓ Test farmer already exists")
    
    # Test Buyer
    if not User.objects.filter(username='testbuyer').exists():
        try:
            buyer = User.objects.create_user(
                username='testbuyer',
                email='buyer@test.com',
                password='buyer123',
                user_type='Buyer',
                first_name='Jane',
                last_name='TestBuyer',
                phone_number='+237 698 765 432',
                is_approved=True  # Auto-approved
            )
            
            BuyerProfile.objects.create(
                buyer=buyer,
                location='Yaounde, Cameroon'
            )
            
            print(f"   ✅ Test buyer created: {buyer.username}")
            print(f"   📧 Email: buyer@test.com")
            print(f"   🔑 Password: buyer123")
        except Exception as e:
            print(f"   ❌ Error creating test buyer: {e}")
    else:
        print("   ✓ Test buyer already exists")

def main():
    """Main setup function"""
    print("🚀 Farm2Market MySQL Setup")
    print("=" * 50)
    
    # Step 1: Check MySQL connection
    print("\n1️⃣ Checking MySQL connection...")
    if not check_mysql_connection():
        print("\n❌ Setup failed: Cannot connect to MySQL")
        print("Please ensure:")
        print("- MySQL server is running")
        print("- Username: root")
        print("- Password: Abdel@ictu2023")
        print("- Port: 3306")
        return False
    
    # Step 2: Create database
    print("\n2️⃣ Setting up database...")
    if not create_database_if_not_exists():
        print("\n❌ Setup failed: Cannot create database")
        return False
    
    # Step 3: Setup Django
    print("\n3️⃣ Setting up Django...")
    if not setup_django():
        print("\n❌ Setup failed: Django setup error")
        return False
    
    # Success message
    print("\n" + "=" * 50)
    print("🎉 SETUP COMPLETE!")
    print("=" * 50)
    print("\n📋 What was created:")
    print("✅ MySQL database: farmtomarket")
    print("✅ Django tables and migrations")
    print("✅ Superuser: admin / admin123")
    print("✅ Admin user: farmadmin / farmadmin123")
    print("✅ Test farmer: testfarmer / farmer123 (pending approval)")
    print("✅ Test buyer: testbuyer / buyer123")
    print("✅ Sample product categories")
    
    print("\n🚀 Next steps:")
    print("1. Start Django server:")
    print("   python manage.py runserver")
    print("\n2. Access admin panel:")
    print("   http://localhost:8000/admin/")
    print("   Login: admin / admin123")
    print("\n3. Test farmer registration:")
    print("   http://localhost:8000/test-registration.html")
    print("\n4. Approve farmers in admin panel")
    print("\n5. Test farmer dashboard:")
    print("   http://localhost:8000/farmer dashboard.html")
    
    return True

if __name__ == '__main__':
    main()
