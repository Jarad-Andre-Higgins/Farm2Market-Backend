#!/usr/bin/env python
"""
Simple test data creation for Farm2Market
"""
import os
import sys
import django

# Set up Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import *
from django.contrib.auth.hashers import make_password

def create_simple_test_data():
    """Create basic test data"""
    print("🌱 Creating simple test data...")
    
    # Create categories
    categories = ['Vegetables', 'Fruits', 'Grains']
    for cat_name in categories:
        category, created = Category.objects.get_or_create(name=cat_name)
        if created:
            print(f"✅ Created category: {cat_name}")
    
    # Create a test farmer
    farmer, created = CustomUser.objects.get_or_create(
        email='testfarmer@farm.com',
        defaults={
            'username': 'testfarmer',
            'first_name': 'Test',
            'last_name': 'Farmer',
            'phone_number': '1234567890',
            'user_type': 'Farmer',
            'is_approved': True,
            'password': make_password('farmer123')
        }
    )
    
    if created:
        print(f"✅ Created farmer: {farmer.first_name} {farmer.last_name}")
        
        # Create farmer profile
        FarmerProfile.objects.get_or_create(
            farmer=farmer,
            defaults={
                'location': 'Douala, Cameroon',
                'trust_badge': True
            }
        )
    
    # Create a test buyer
    buyer, created = CustomUser.objects.get_or_create(
        email='testbuyer@buyer.com',
        defaults={
            'username': 'testbuyer',
            'first_name': 'Test',
            'last_name': 'Buyer',
            'phone_number': '1234567891',
            'user_type': 'Buyer',
            'is_approved': True,
            'password': make_password('buyer123')
        }
    )
    
    if created:
        print(f"✅ Created buyer: {buyer.first_name} {buyer.last_name}")
        
        # Create buyer profile
        BuyerProfile.objects.get_or_create(
            buyer=buyer,
            defaults={
                'location': 'Douala, Cameroon',
                'delivery_address': 'Douala, Cameroon',
                'preferred_delivery_method': 'delivery'
            }
        )
    
    # Create test products
    products = [
        {'name': 'Fresh Tomatoes', 'price': 500, 'quantity': 50, 'unit': 'kg', 'category': 'Vegetables'},
        {'name': 'Sweet Bananas', 'price': 200, 'quantity': 100, 'unit': 'bunches', 'category': 'Fruits'},
        {'name': 'White Rice', 'price': 800, 'quantity': 20, 'unit': 'bags', 'category': 'Grains'}
    ]
    
    for product_data in products:
        listing, created = FarmerListing.objects.get_or_create(
            farmer=farmer,
            product_name=product_data['name'],
            defaults={
                'description': f'Fresh {product_data["name"]} from local farm',
                'price': product_data['price'],
                'quantity': product_data['quantity'],
                'quantity_unit': product_data['unit'],
                'status': 'Available',
                'image_url': f'https://via.placeholder.com/300x200?text={product_data["name"].replace(" ", "+")}'
            }
        )
        
        if created:
            print(f"✅ Created product: {product_data['name']}")
            
            # Add category through ProductCategory
            category = Category.objects.get(name=product_data['category'])
            ProductCategory.objects.get_or_create(
                listing=listing,
                category=category
            )
    
    print("\n🎉 Simple test data created successfully!")
    print(f"📊 Summary:")
    print(f"  • Categories: {Category.objects.count()}")
    print(f"  • Users: {CustomUser.objects.count()}")
    print(f"  • Products: {FarmerListing.objects.count()}")
    print(f"\n🔑 Test Credentials:")
    print(f"  Farmer: testfarmer@farm.com / farmer123")
    print(f"  Buyer: testbuyer@buyer.com / buyer123")

if __name__ == '__main__':
    create_simple_test_data()
