#!/usr/bin/env python
"""
Create test data for Farm2Market API testing
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import *
from django.contrib.auth.hashers import make_password

def create_test_data():
    """Create comprehensive test data"""
    print("🌱 Creating Farm2Market test data...")
    
    # 1. Create test categories
    print("📂 Creating categories...")
    categories = [
        'Vegetables', 'Fruits', 'Grains', 'Legumes', 'Herbs', 'Dairy', 'Poultry', 'Livestock'
    ]
    
    for cat_name in categories:
        category, created = Category.objects.get_or_create(
            name=cat_name
        )
        if created:
            print(f"  ✅ Created category: {cat_name}")
    
    # 2. Create test farmers
    print("🚜 Creating test farmers...")
    farmers_data = [
        {
            'username': 'farmer_john',
            'email': 'john@farm.com',
            'first_name': 'John',
            'last_name': 'Smith',
            'phone': '1234567890',
            'location': 'Douala, Cameroon'
        },
        {
            'username': 'farmer_mary',
            'email': 'mary@farm.com',
            'first_name': 'Mary',
            'last_name': 'Johnson',
            'phone': '1234567891',
            'location': 'Yaoundé, Cameroon'
        },
        {
            'username': 'farmer_peter',
            'email': 'peter@farm.com',
            'first_name': 'Peter',
            'last_name': 'Brown',
            'phone': '1234567892',
            'location': 'Bamenda, Cameroon'
        }
    ]
    
    created_farmers = []
    for farmer_data in farmers_data:
        farmer, created = CustomUser.objects.get_or_create(
            email=farmer_data['email'],
            defaults={
                'username': farmer_data['username'],
                'first_name': farmer_data['first_name'],
                'last_name': farmer_data['last_name'],
                'phone_number': farmer_data['phone'],
                'user_type': 'Farmer',
                'is_approved': True,
                'password': make_password('farmer123')
            }
        )
        
        if created:
            print(f"  ✅ Created farmer: {farmer.first_name} {farmer.last_name}")
            
            # Create farmer profile
            profile, profile_created = FarmerProfile.objects.get_or_create(
                farmer=farmer,
                defaults={
                    'location': farmer_data['location'],
                    'trust_badge': True
                }
            )
            
        created_farmers.append(farmer)
    
    # 3. Create test buyers
    print("🛒 Creating test buyers...")
    buyers_data = [
        {
            'username': 'buyer_alice',
            'email': 'alice@buyer.com',
            'first_name': 'Alice',
            'last_name': 'Wilson',
            'phone': '1234567893'
        },
        {
            'username': 'buyer_bob',
            'email': 'bob@buyer.com',
            'first_name': 'Bob',
            'last_name': 'Davis',
            'phone': '1234567894'
        }
    ]
    
    for buyer_data in buyers_data:
        buyer, created = CustomUser.objects.get_or_create(
            email=buyer_data['email'],
            defaults={
                'username': buyer_data['username'],
                'first_name': buyer_data['first_name'],
                'last_name': buyer_data['last_name'],
                'phone_number': buyer_data['phone'],
                'user_type': 'Buyer',
                'is_approved': True,
                'password': make_password('buyer123')
            }
        )
        
        if created:
            print(f"  ✅ Created buyer: {buyer.first_name} {buyer.last_name}")
            
            # Create buyer profile
            profile, profile_created = BuyerProfile.objects.get_or_create(
                buyer=buyer,
                defaults={
                    'location': 'Douala, Cameroon',
                    'delivery_address': 'Douala, Cameroon',
                    'preferred_delivery_method': 'delivery',
                    'delivery_time_preferences': 'Morning',
                    'email_notifications': True
                }
            )
    
    # 4. Create test products
    print("🌾 Creating test products...")
    products_data = [
        {
            'product_name': 'Fresh Tomatoes',
            'description': 'Organic red tomatoes, freshly harvested',
            'price': 500,
            'quantity': 50,
            'quantity_unit': 'kg',
            'category': 'Vegetables'
        },
        {
            'product_name': 'Sweet Corn',
            'description': 'Yellow sweet corn, perfect for cooking',
            'price': 300,
            'quantity': 30,
            'quantity_unit': 'kg',
            'category': 'Vegetables'
        },
        {
            'product_name': 'Bananas',
            'description': 'Ripe yellow bananas, sweet and nutritious',
            'price': 200,
            'quantity': 100,
            'quantity_unit': 'bunches',
            'category': 'Fruits'
        },
        {
            'product_name': 'Rice',
            'description': 'Local white rice, high quality',
            'price': 800,
            'quantity': 20,
            'quantity_unit': 'bags',
            'category': 'Grains'
        },
        {
            'product_name': 'Beans',
            'description': 'Red kidney beans, protein-rich',
            'price': 600,
            'quantity': 25,
            'quantity_unit': 'kg',
            'category': 'Legumes'
        }
    ]
    
    for i, product_data in enumerate(products_data):
        farmer = created_farmers[i % len(created_farmers)]
        category = Category.objects.get(name=product_data['category'])
        
        listing, created = FarmerListing.objects.get_or_create(
            farmer=farmer,
            product_name=product_data['product_name'],
            defaults={
                'description': product_data['description'],
                'price': product_data['price'],
                'quantity': product_data['quantity'],
                'quantity_unit': product_data['quantity_unit'],
                'status': 'Available',
                'image_url': f'https://via.placeholder.com/300x200?text={product_data["product_name"].replace(" ", "+")}'
            }
        )
        
        if created:
            print(f"  ✅ Created product: {product_data['product_name']} by {farmer.first_name}")
            
            # Add category to listing
            listing.categories.add(category)
    
    print("\n🎉 Test data creation completed!")
    print(f"📊 Summary:")
    print(f"  • Categories: {Category.objects.count()}")
    print(f"  • Farmers: {CustomUser.objects.filter(user_type='Farmer').count()}")
    print(f"  • Buyers: {CustomUser.objects.filter(user_type='Buyer').count()}")
    print(f"  • Products: {FarmerListing.objects.count()}")
    
    print(f"\n🔑 Test Credentials:")
    print(f"  Farmers: farmer_john@farm.com / farmer123")
    print(f"  Buyers: alice@buyer.com / buyer123")
    print(f"  Admin: admin@farm2market.com / admin123")

if __name__ == '__main__':
    create_test_data()
