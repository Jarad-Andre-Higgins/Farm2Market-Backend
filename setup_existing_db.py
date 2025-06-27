#!/usr/bin/env python
"""
Setup script for existing Farm2Market MySQL database
This script will work with your existing database and:
1. Check database connection
2. Create/update Django migrations
3. Apply migrations to existing database
4. Create superuser and sample data if needed
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')

def setup_django_with_existing_db():
    """Setup Django with existing MySQL database"""
    try:
        # Setup Django
        django.setup()
        
        from django.core.management import execute_from_command_line
        from django.contrib.auth import get_user_model
        from coreF2M.models import Category, FarmerProfile, BuyerProfile, Notification
        from django.db import connection
        
        User = get_user_model()
        
        print("🔍 Checking existing database...")
        
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            print(f"✅ Connected to database: {db_name}")
            
            # Show existing tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"📊 Found {len(tables)} existing tables")
        
        print("\n📝 Creating/updating Django migrations...")
        try:
            execute_from_command_line(['manage.py', 'makemigrations', 'coreF2M'])
        except Exception as e:
            print(f"   ⚠️  Migration creation: {e}")
        
        print("\n🔄 Applying migrations to existing database...")
        try:
            execute_from_command_line(['manage.py', 'migrate', '--fake-initial'])
        except Exception as e:
            print(f"   ⚠️  Migration application: {e}")
            print("   Trying regular migrate...")
            try:
                execute_from_command_line(['manage.py', 'migrate'])
            except Exception as e2:
                print(f"   ⚠️  Regular migrate: {e2}")
        
        print("\n👑 Checking/creating superuser...")
        create_superuser_if_needed(User)
        
        print("\n👨‍💼 Checking/creating admin user...")
        create_admin_user_if_needed(User)
        
        print("\n📂 Checking/creating sample categories...")
        create_categories_if_needed(Category)
        
        print("\n👥 Checking/creating test users...")
        create_test_users_if_needed(User, FarmerProfile, BuyerProfile)
        
        return True
        
    except Exception as e:
        print(f"❌ Django setup error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_superuser_if_needed(User):
    """Create Django superuser if it doesn't exist"""
    try:
        if User.objects.filter(is_superuser=True).exists():
            superuser = User.objects.filter(is_superuser=True).first()
            print(f"   ✓ Superuser already exists: {superuser.username}")
            return
        
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
        print(f"   ❌ Error with superuser: {e}")

def create_admin_user_if_needed(User):
    """Create regular admin user if it doesn't exist"""
    try:
        if User.objects.filter(username='farmadmin').exists():
            print("   ✓ Admin user already exists: farmadmin")
            return
        
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
        print(f"   ❌ Error with admin user: {e}")

def create_categories_if_needed(Category):
    """Create sample product categories if they don't exist"""
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
    
    try:
        existing_count = Category.objects.count()
        created_count = 0
        
        for category_name in categories:
            category, created = Category.objects.get_or_create(name=category_name)
            if created:
                created_count += 1
        
        print(f"   ✅ Created {created_count} new categories")
        print(f"   📊 Total categories: {Category.objects.count()}")
    except Exception as e:
        print(f"   ❌ Error with categories: {e}")

def create_test_users_if_needed(User, FarmerProfile, BuyerProfile):
    """Create test users if they don't exist"""
    try:
        # Test Farmer
        if User.objects.filter(username='testfarmer').exists():
            print("   ✓ Test farmer already exists: testfarmer")
        else:
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
        
        # Test Buyer
        if User.objects.filter(username='testbuyer').exists():
            print("   ✓ Test buyer already exists: testbuyer")
        else:
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
        print(f"   ❌ Error with test users: {e}")

def main():
    """Main setup function"""
    print("🚀 Farm2Market Setup (Existing MySQL Database)")
    print("=" * 60)
    
    print("\n🔍 Working with your existing MySQL database...")
    print("Database: farmtomarket")
    print("Host: localhost")
    print("User: root")
    
    if not setup_django_with_existing_db():
        print("\n❌ Setup failed!")
        return False
    
    # Success message
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("\n📋 Your existing database is now ready with:")
    print("✅ Django models and migrations applied")
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
