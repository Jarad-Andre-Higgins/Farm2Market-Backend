#!/usr/bin/env python
"""
Create test reservations with buyer names for farmer dashboard testing
"""
import os
import sys
import django
from decimal import Decimal

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import (
    CustomUser, FarmerProfile, BuyerProfile, Category, 
    FarmerListing, Reservation, ProductCategory
)

def create_test_data_with_reservations():
    print("🌱 Creating test data with buyer reservations...")
    
    try:
        # Get or create test users
        farmer_user = CustomUser.objects.get(email='testfarmer@farm.com')
        buyer_user = CustomUser.objects.get(email='testbuyer@buyer.com')
        
        print(f"✅ Found farmer: {farmer_user.email}")
        print(f"✅ Found buyer: {buyer_user.email}")
        
        # Create categories
        categories = ['Vegetables', 'Fruits', 'Grains', 'Herbs']
        for cat_name in categories:
            category, created = Category.objects.get_or_create(name=cat_name)
            if created:
                print(f"✅ Created category: {cat_name}")
        
        # Create product categories for farmer
        vegetable_cat = Category.objects.get(name='Vegetables')
        fruit_cat = Category.objects.get(name='Fruits')
        
        # Create farmer listings
        listings_data = [
            {
                'product_name': 'Fresh Tomatoes',
                'price': Decimal('800.00'),
                'quantity': 50,
                'quantity_unit': 'kg',
                'description': 'Fresh organic tomatoes from our farm',
                'status': 'Available'
            },
            {
                'product_name': 'Sweet Bananas',
                'price': Decimal('400.00'),
                'quantity': 30,
                'quantity_unit': 'kg',
                'description': 'Sweet ripe bananas perfect for eating',
                'status': 'Available'
            },
            {
                'product_name': 'Organic Carrots',
                'price': Decimal('600.00'),
                'quantity': 25,
                'quantity_unit': 'kg',
                'description': 'Organic carrots grown without pesticides',
                'status': 'Available'
            }
        ]

        created_listings = []
        for listing_data in listings_data:
            listing, created = FarmerListing.objects.get_or_create(
                farmer=farmer_user,
                product_name=listing_data['product_name'],
                defaults=listing_data
            )
            if created:
                print(f"✅ Created listing: {listing.product_name}")

                # Create product category relationship
                ProductCategory.objects.get_or_create(
                    listing=listing,
                    category=vegetable_cat if 'Tomatoes' in listing.product_name or 'Carrots' in listing.product_name else fruit_cat
                )

            created_listings.append(listing)
        
        # Create test reservations with buyer names
        reservations_data = [
            {
                'listing': created_listings[0],  # Tomatoes
                'quantity': 10,
                'delivery_address': '123 Buyer Street, Yaoundé',
                'status': 'pending',
                'buyer_notes': 'Please deliver fresh tomatoes for my restaurant'
            },
            {
                'listing': created_listings[1],  # Bananas
                'quantity': 5,
                'delivery_address': '456 Market Road, Douala',
                'status': 'approved',
                'buyer_notes': 'Need sweet bananas for fruit salad'
            },
            {
                'listing': created_listings[2],  # Carrots
                'quantity': 8,
                'delivery_address': '789 Food Avenue, Bamenda',
                'status': 'pending',
                'buyer_notes': 'Organic carrots for baby food preparation'
            }
        ]

        for reservation_data in reservations_data:
            # Calculate total amount
            unit_price = reservation_data['listing'].price
            total_amount = unit_price * reservation_data['quantity']

            reservation, created = Reservation.objects.get_or_create(
                buyer=buyer_user,
                listing=reservation_data['listing'],
                quantity=reservation_data['quantity'],
                defaults={
                    'unit_price': unit_price,
                    'total_amount': total_amount,
                    'delivery_method': 'delivery',
                    'delivery_address': reservation_data['delivery_address'],
                    'status': reservation_data['status'],
                    'buyer_notes': reservation_data['buyer_notes']
                }
            )

            if created:
                print(f"✅ Created reservation: {buyer_user.first_name} {buyer_user.last_name} -> {reservation.listing.product_name}")
                print(f"   Quantity: {reservation.quantity}kg | Total: {total_amount} FCFA | Status: {reservation.status}")
        
        # Create additional test buyers for more realistic data
        additional_buyers = [
            {
                'email': 'marie.buyer@email.com',
                'username': 'mariebuyer',
                'first_name': 'Marie',
                'last_name': 'Ngozi',
                'password': 'buyer123'
            },
            {
                'email': 'paul.customer@email.com',
                'username': 'paulcustomer',
                'first_name': 'Paul',
                'last_name': 'Mbeki',
                'password': 'buyer123'
            }
        ]
        
        for buyer_data in additional_buyers:
            buyer, created = CustomUser.objects.get_or_create(
                email=buyer_data['email'],
                defaults={
                    'username': buyer_data['username'],
                    'first_name': buyer_data['first_name'],
                    'last_name': buyer_data['last_name'],
                    'user_type': 'Buyer',
                    'is_active': True,
                    'is_approved': True
                }
            )
            
            if created:
                buyer.set_password(buyer_data['password'])
                buyer.save()
                print(f"✅ Created additional buyer: {buyer.first_name} {buyer.last_name}")
                
                # Create buyer profile
                BuyerProfile.objects.get_or_create(
                    buyer=buyer,
                    defaults={'location': 'Cameroon'}
                )
                
                # Create a reservation from this buyer
                if created_listings:
                    listing = created_listings[0]  # Tomatoes
                    unit_price = listing.price
                    quantity = 3
                    total_amount = unit_price * quantity

                    reservation, res_created = Reservation.objects.get_or_create(
                        buyer=buyer,
                        listing=listing,
                        quantity=quantity,
                        defaults={
                            'unit_price': unit_price,
                            'total_amount': total_amount,
                            'delivery_method': 'delivery',
                            'delivery_address': f'{buyer.first_name} Home, Cameroon',
                            'status': 'pending',
                            'buyer_notes': f'Order from {buyer.first_name}'
                        }
                    )

                    if res_created:
                        print(f"✅ Created reservation from {buyer.first_name}: {listing.product_name}")
        
        print("\n🎉 Test data with buyer reservations created successfully!")
        print("\n📊 Summary:")
        print(f"  • Farmers: {CustomUser.objects.filter(user_type='Farmer').count()}")
        print(f"  • Buyers: {CustomUser.objects.filter(user_type='Buyer').count()}")
        print(f"  • Products: {FarmerListing.objects.count()}")
        print(f"  • Reservations: {Reservation.objects.count()}")
        
        print("\n🔑 Test Credentials:")
        print("🌱 Farmer: testfarmer@farm.com / farmer123")
        print("🛒 Buyer: testbuyer@buyer.com / buyer123")
        print("🛒 Additional Buyers:")
        for buyer_data in additional_buyers:
            print(f"   {buyer_data['email']} / {buyer_data['password']}")
        
        print("\n✅ Farmer dashboard will now show REAL buyer names and reservations!")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_test_data_with_reservations()
