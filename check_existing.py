#!/usr/bin/env python
"""
Check existing Farm2Market database and add only what's missing
This script will:
1. Check what's already in your database
2. Show existing users and data
3. Add only missing components
4. Preserve all existing data
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')

def check_existing_database():
    """Check what's already in the database"""
    try:
        # Setup Django
        django.setup()
        
        from django.contrib.auth import get_user_model
        from coreF2M.models import Category, FarmerProfile, BuyerProfile, Notification
        from django.db import connection
        
        User = get_user_model()
        
        print("🔍 CHECKING EXISTING DATABASE")
        print("=" * 50)
        
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            print(f"📊 Database: {db_name}")
            
            # Show existing tables
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            print(f"📋 Tables found: {len(tables)}")
            for table in tables:
                print(f"   - {table}")
        
        print("\n👥 EXISTING USERS:")
        print("-" * 30)
        
        try:
            users = User.objects.all()
            if users.exists():
                for user in users:
                    status = "✅ Approved" if user.is_approved else "⏳ Pending"
                    super_status = "👑 SUPERUSER" if user.is_superuser else ""
                    print(f"   {user.username} ({user.user_type}) - {user.email} {status} {super_status}")
            else:
                print("   No users found")
        except Exception as e:
            print(f"   ❌ Error checking users: {e}")
        
        print("\n📂 EXISTING CATEGORIES:")
        print("-" * 30)
        
        try:
            categories = Category.objects.all()
            if categories.exists():
                for category in categories:
                    print(f"   - {category.name}")
            else:
                print("   No categories found")
        except Exception as e:
            print(f"   ❌ Error checking categories: {e}")
        
        print("\n🏠 EXISTING PROFILES:")
        print("-" * 30)
        
        try:
            farmer_profiles = FarmerProfile.objects.all()
            buyer_profiles = BuyerProfile.objects.all()
            print(f"   Farmer profiles: {farmer_profiles.count()}")
            print(f"   Buyer profiles: {buyer_profiles.count()}")
        except Exception as e:
            print(f"   ❌ Error checking profiles: {e}")
        
        # Now add missing components
        print("\n🔧 ADDING MISSING COMPONENTS:")
        print("-" * 40)
        
        add_missing_categories(Category)
        add_missing_test_users(User, FarmerProfile, BuyerProfile)
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_missing_categories(Category):
    """Add categories only if they don't exist"""
    default_categories = [
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
        added_count = 0
        for category_name in default_categories:
            category, created = Category.objects.get_or_create(name=category_name)
            if created:
                added_count += 1
                print(f"   ✅ Added category: {category_name}")
        
        if added_count == 0:
            print("   ✓ All default categories already exist")
        else:
            print(f"   📊 Added {added_count} new categories")
            
    except Exception as e:
        print(f"   ❌ Error with categories: {e}")

def add_missing_test_users(User, FarmerProfile, BuyerProfile):
    """Add test users only if they don't exist"""
    try:
        # Check for test farmer
        if not User.objects.filter(username='testfarmer').exists():
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
            
            print(f"   ✅ Added test farmer: testfarmer / farmer123 (pending approval)")
        else:
            print("   ✓ Test farmer already exists")
        
        # Check for test buyer
        if not User.objects.filter(username='testbuyer').exists():
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
            
            print(f"   ✅ Added test buyer: testbuyer / buyer123")
        else:
            print("   ✓ Test buyer already exists")
            
    except Exception as e:
        print(f"   ❌ Error with test users: {e}")

def show_login_info(User):
    """Show login information for existing users"""
    print("\n🔑 LOGIN INFORMATION:")
    print("-" * 30)
    
    try:
        # Show superuser info
        superusers = User.objects.filter(is_superuser=True)
        for su in superusers:
            print(f"👑 SUPERUSER: {su.username}")
            print(f"   Email: {su.email}")
            print(f"   Use for admin panel: http://localhost:8000/admin/")
        
        # Show admin users
        admins = User.objects.filter(user_type='Admin', is_superuser=False)
        for admin in admins:
            print(f"👨‍💼 ADMIN: {admin.username}")
            print(f"   Email: {admin.email}")
        
        # Show test users
        test_farmer = User.objects.filter(username='testfarmer').first()
        if test_farmer:
            status = "✅ Approved" if test_farmer.is_approved else "⏳ Pending approval"
            print(f"🧑‍🌾 TEST FARMER: testfarmer / farmer123 ({status})")
        
        test_buyer = User.objects.filter(username='testbuyer').first()
        if test_buyer:
            print(f"🛒 TEST BUYER: testbuyer / buyer123")
            
    except Exception as e:
        print(f"❌ Error showing login info: {e}")

def main():
    """Main function"""
    print("🚀 Farm2Market Database Check")
    print("=" * 50)
    
    if not check_existing_database():
        print("\n❌ Database check failed!")
        return False
    
    # Show login information
    from django.contrib.auth import get_user_model
    User = get_user_model()
    show_login_info(User)
    
    print("\n" + "=" * 50)
    print("🎉 DATABASE CHECK COMPLETE!")
    print("=" * 50)
    
    print("\n🚀 NEXT STEPS:")
    print("1. Start Django server:")
    print("   python manage.py runserver")
    print("\n2. Access admin panel with your existing superuser:")
    print("   http://localhost:8000/admin/")
    print("\n3. Test farmer registration:")
    print("   http://localhost:8000/test-registration.html")
    print("\n4. Test farmer dashboard:")
    print("   http://localhost:8000/farmer dashboard.html")
    print("\n5. Approve test farmer in admin panel if needed")
    
    return True

if __name__ == '__main__':
    main()
