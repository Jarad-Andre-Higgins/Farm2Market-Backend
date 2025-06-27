#!/usr/bin/env python
"""
Quick script to create test users for Agriport testing
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import CustomUser, FarmerProfile, BuyerProfile, Category, ProductCategory

def create_test_users():
    print("🌱 Creating test users for Agriport...")
    
    # Create categories first
    categories = [
        'Vegetables', 'Fruits', 'Grains', 'Dairy', 'Meat', 'Herbs', 'Nuts', 'Spices'
    ]
    
    for cat_name in categories:
        category, created = Category.objects.get_or_create(
            name=cat_name
        )
        if created:
            print(f"✅ Created category: {cat_name}")
    
    # Create test buyer
    try:
        buyer_user, created = CustomUser.objects.get_or_create(
            email='testbuyer@buyer.com',
            defaults={
                'username': 'testbuyer',
                'first_name': 'Test',
                'last_name': 'Buyer',
                'user_type': 'Buyer',
                'is_active': True,
                'is_verified': True
            }
        )
        if created:
            buyer_user.set_password('buyer123')
            buyer_user.save()
            print("✅ Created test buyer user")
        else:
            # Update password in case it was different
            buyer_user.set_password('buyer123')
            buyer_user.is_active = True
            buyer_user.is_verified = True
            buyer_user.save()
            print("✅ Updated test buyer user")
        
        # Create buyer profile
        buyer_profile, created = BuyerProfile.objects.get_or_create(
            user=buyer_user,
            defaults={
                'phone_number': '+237123456789',
                'delivery_address': '123 Test Street, Yaoundé, Cameroon',
                'preferred_delivery_time': 'Morning'
            }
        )
        if created:
            print("✅ Created buyer profile")
            
    except Exception as e:
        print(f"❌ Error creating buyer: {e}")
    
    # Create test farmer
    try:
        farmer_user, created = CustomUser.objects.get_or_create(
            email='testfarmer@farm.com',
            defaults={
                'username': 'testfarmer',
                'first_name': 'Test',
                'last_name': 'Farmer',
                'user_type': 'Farmer',
                'is_active': True,
                'is_verified': True
            }
        )
        if created:
            farmer_user.set_password('farmer123')
            farmer_user.save()
            print("✅ Created test farmer user")
        else:
            # Update password and ensure active
            farmer_user.set_password('farmer123')
            farmer_user.is_active = True
            farmer_user.is_verified = True
            farmer_user.save()
            print("✅ Updated test farmer user")
        
        # Create farmer profile
        farmer_profile, created = FarmerProfile.objects.get_or_create(
            user=farmer_user,
            defaults={
                'phone_number': '+237987654321',
                'location': 'Bamenda, Northwest Region, Cameroon',
                'farm_description': 'Organic vegetable farm specializing in fresh produce',
                'farm_size': '5 hectares',
                'farming_experience': '10 years',
                'trust_badge': True
            }
        )
        if created:
            print("✅ Created farmer profile")
            
    except Exception as e:
        print(f"❌ Error creating farmer: {e}")
    
    # Create admin user
    try:
        admin_user, created = CustomUser.objects.get_or_create(
            email='admin@agriport.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'user_type': 'Admin',
                'is_active': True,
                'is_verified': True,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            print("✅ Created admin user")
        else:
            admin_user.set_password('admin123')
            admin_user.is_active = True
            admin_user.is_verified = True
            admin_user.save()
            print("✅ Updated admin user")
            
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
    
    print("\n🎉 Test users created successfully!")
    print("\n🔑 Test Credentials:")
    print("👤 Buyer: testbuyer@buyer.com / buyer123")
    print("🌱 Farmer: testfarmer@farm.com / farmer123")
    print("⚙️ Admin: admin@agriport.com / admin123")
    print("\n✅ All users are active and verified!")

if __name__ == '__main__':
    create_test_users()
