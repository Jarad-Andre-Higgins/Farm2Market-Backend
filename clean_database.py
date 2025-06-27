#!/usr/bin/env python
"""
Clean up all redundant database entries and create fresh test data
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import (
    CustomUser, FarmerProfile, BuyerProfile, Category, 
    FarmerListing, ProductCategory, Reservation, UrgentSale,
    UrgentSaleReservation, Transaction, Notification, Review
)

def clean_all_database_entries():
    print("🧹 CLEANING ALL DATABASE ENTRIES...")
    print("⚠️  This will delete ALL users and data!")
    
    # Count current entries
    print(f"\n📊 Current Database State:")
    print(f"   Users: {CustomUser.objects.count()}")
    print(f"   Farmer Profiles: {FarmerProfile.objects.count()}")
    print(f"   Buyer Profiles: {BuyerProfile.objects.count()}")
    print(f"   Categories: {Category.objects.count()}")
    print(f"   Farmer Listings: {FarmerListing.objects.count()}")
    print(f"   Reservations: {Reservation.objects.count()}")
    print(f"   Notifications: {Notification.objects.count()}")
    print(f"   Transactions: {Transaction.objects.count()}")
    print(f"   Reviews: {Review.objects.count()}")
    print(f"   Urgent Sales: {UrgentSale.objects.count()}")
    
    # Delete all data in correct order (respecting foreign key constraints)
    print(f"\n🗑️  Deleting all entries...")
    
    # Delete dependent objects first
    deleted_counts = {}
    
    # Reviews (depends on users and listings)
    count = Review.objects.count()
    Review.objects.all().delete()
    deleted_counts['Reviews'] = count
    
    # Urgent Sale Reservations (depends on urgent sales and users)
    count = UrgentSaleReservation.objects.count()
    UrgentSaleReservation.objects.all().delete()
    deleted_counts['Urgent Sale Reservations'] = count
    
    # Transactions (depends on reservations and users)
    count = Transaction.objects.count()
    Transaction.objects.all().delete()
    deleted_counts['Transactions'] = count
    
    # Reservations (depends on listings and users)
    count = Reservation.objects.count()
    Reservation.objects.all().delete()
    deleted_counts['Reservations'] = count
    
    # Urgent Sales (depends on listings)
    count = UrgentSale.objects.count()
    UrgentSale.objects.all().delete()
    deleted_counts['Urgent Sales'] = count
    
    # Product Categories (depends on listings and categories)
    count = ProductCategory.objects.count()
    ProductCategory.objects.all().delete()
    deleted_counts['Product Categories'] = count
    
    # Farmer Listings (depends on users)
    count = FarmerListing.objects.count()
    FarmerListing.objects.all().delete()
    deleted_counts['Farmer Listings'] = count
    
    # Notifications (depends on users)
    count = Notification.objects.count()
    Notification.objects.all().delete()
    deleted_counts['Notifications'] = count
    
    # User Profiles (depends on users)
    count = FarmerProfile.objects.count()
    FarmerProfile.objects.all().delete()
    deleted_counts['Farmer Profiles'] = count
    
    count = BuyerProfile.objects.count()
    BuyerProfile.objects.all().delete()
    deleted_counts['Buyer Profiles'] = count
    
    # Categories (independent)
    count = Category.objects.count()
    Category.objects.all().delete()
    deleted_counts['Categories'] = count
    
    # Users (main table)
    count = CustomUser.objects.count()
    CustomUser.objects.all().delete()
    deleted_counts['Users'] = count
    
    # Print deletion summary
    print(f"\n✅ Deletion Summary:")
    for model, count in deleted_counts.items():
        if count > 0:
            print(f"   ✅ Deleted {count} {model}")
    
    print(f"\n🎉 Database cleaned successfully!")
    
    # Verify cleanup
    print(f"\n📊 Final Database State:")
    print(f"   Users: {CustomUser.objects.count()}")
    print(f"   Farmer Profiles: {FarmerProfile.objects.count()}")
    print(f"   Buyer Profiles: {BuyerProfile.objects.count()}")
    print(f"   Categories: {Category.objects.count()}")
    print(f"   Farmer Listings: {FarmerListing.objects.count()}")
    print(f"   Reservations: {Reservation.objects.count()}")
    print(f"   Notifications: {Notification.objects.count()}")
    print(f"   Transactions: {Transaction.objects.count()}")
    print(f"   Reviews: {Review.objects.count()}")
    print(f"   Urgent Sales: {UrgentSale.objects.count()}")
    
    if CustomUser.objects.count() == 0:
        print(f"\n✅ Database is completely clean!")
    else:
        print(f"\n⚠️  Some entries remain - check for issues")

def create_essential_test_data():
    print(f"\n🌱 Creating essential test data...")
    
    from decimal import Decimal
    
    # Create essential categories
    categories = ['Vegetables', 'Fruits', 'Grains', 'Herbs']
    created_categories = []
    
    for cat_name in categories:
        category = Category.objects.create(name=cat_name)
        created_categories.append(category)
        print(f"✅ Created category: {cat_name}")
    
    # Create ONE admin user
    admin = CustomUser.objects.create_user(
        email='admin@agriport.com',
        username='admin',
        password='admin123',
        first_name='Admin',
        last_name='User',
        user_type='Admin',
        is_active=True,
        is_approved=True,
        is_staff=True,
        is_superuser=True
    )
    print(f"✅ Created admin: {admin.email}")
    
    # Create ONE test farmer
    farmer = CustomUser.objects.create_user(
        email='farmer@agriport.com',
        username='farmer',
        password='farmer123',
        first_name='Test',
        last_name='Farmer',
        user_type='Farmer',
        is_active=True,
        is_approved=True
    )
    
    farmer_profile = FarmerProfile.objects.create(
        farmer=farmer,
        location='Bamenda, Cameroon',
        trust_badge=True
    )
    print(f"✅ Created farmer: {farmer.email}")
    
    # Create ONE test buyer
    buyer = CustomUser.objects.create_user(
        email='buyer@agriport.com',
        username='buyer',
        password='buyer123',
        first_name='Test',
        last_name='Buyer',
        user_type='Buyer',
        is_active=True,
        is_approved=True
    )
    
    buyer_profile = BuyerProfile.objects.create(
        buyer=buyer,
        location='Yaoundé, Cameroon'
    )
    print(f"✅ Created buyer: {buyer.email}")
    
    # Create sample products
    products = [
        {
            'product_name': 'Fresh Tomatoes',
            'price': Decimal('800.00'),
            'quantity': 50,
            'quantity_unit': 'kg',
            'description': 'Fresh organic tomatoes',
            'category': created_categories[0]  # Vegetables
        },
        {
            'product_name': 'Sweet Bananas',
            'price': Decimal('400.00'),
            'quantity': 30,
            'quantity_unit': 'kg',
            'description': 'Sweet ripe bananas',
            'category': created_categories[1]  # Fruits
        }
    ]
    
    created_listings = []
    for product_data in products:
        category = product_data.pop('category')
        listing = FarmerListing.objects.create(
            farmer=farmer,
            **product_data
        )
        
        # Create product category relationship
        ProductCategory.objects.create(
            listing=listing,
            category=category
        )
        
        created_listings.append(listing)
        print(f"✅ Created product: {listing.product_name}")
    
    # Create sample reservations
    for i, listing in enumerate(created_listings):
        reservation = Reservation.objects.create(
            buyer=buyer,
            listing=listing,
            quantity=5,
            unit_price=listing.price,
            total_amount=listing.price * 5,
            delivery_method='delivery',
            delivery_address='Test Address, Cameroon',
            status='pending',
            buyer_notes=f'Test reservation for {listing.product_name}'
        )
        print(f"✅ Created reservation: {buyer.first_name} -> {listing.product_name}")
    
    print(f"\n🎉 Essential test data created successfully!")
    print(f"\n🔑 Clean Test Credentials:")
    print(f"   👑 Admin: admin@agriport.com / admin123")
    print(f"   🌱 Farmer: farmer@agriport.com / farmer123")
    print(f"   🛒 Buyer: buyer@agriport.com / buyer123")

if __name__ == '__main__':
    print("🧹 AGRIPORT DATABASE CLEANUP")
    print("=" * 50)
    
    # Clean everything
    clean_all_database_entries()
    
    # Create fresh essential data
    create_essential_test_data()
    
    print(f"\n" + "=" * 50)
    print(f"✅ DATABASE CLEANUP COMPLETE!")
    print(f"🚀 Ready for clean testing!")
