#!/usr/bin/env python
"""
COMPLETELY CLEAN MySQL Database - Remove ALL data from ALL tables
"""
import os
import sys
import django
from django.db import connection

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

def clean_mysql_database_completely():
    print("🔥 COMPLETELY CLEANING MySQL DATABASE")
    print("⚠️  This will PERMANENTLY DELETE ALL DATA from ALL TABLES!")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        # First, get all table names
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        if not tables:
            print("✅ No tables found - database is already empty")
            return
        
        print(f"📊 Found {len(tables)} tables in database:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
            count = cursor.fetchone()[0]
            print(f"   📋 {table_name}: {count} records")
        
        print(f"\n🗑️  DELETING ALL DATA FROM ALL TABLES...")
        
        # Disable foreign key checks to avoid constraint issues
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        # Truncate all tables (faster than DELETE)
        deleted_counts = {}
        for table in tables:
            table_name = table[0]
            try:
                # Get count before deletion
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
                count = cursor.fetchone()[0]
                
                # Truncate table (removes all data and resets auto-increment)
                cursor.execute(f"TRUNCATE TABLE `{table_name}`;")
                deleted_counts[table_name] = count
                
                print(f"   ✅ Truncated {table_name}: {count} records deleted")
            except Exception as e:
                print(f"   ❌ Error truncating {table_name}: {e}")
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        print(f"\n📊 DELETION SUMMARY:")
        total_deleted = 0
        for table_name, count in deleted_counts.items():
            if count > 0:
                print(f"   🗑️  {table_name}: {count} records deleted")
                total_deleted += count
        
        print(f"\n🎉 TOTAL RECORDS DELETED: {total_deleted}")
        
        # Verify cleanup
        print(f"\n🔍 VERIFYING CLEANUP...")
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        all_empty = True
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"   ⚠️  {table_name}: {count} records remaining")
                all_empty = False
            else:
                print(f"   ✅ {table_name}: EMPTY")
        
        if all_empty:
            print(f"\n✅ ALL TABLES ARE COMPLETELY EMPTY!")
            print(f"🎉 MySQL DATABASE IS 100% CLEAN!")
        else:
            print(f"\n⚠️  Some tables still have data - check for issues")

def reset_auto_increment_counters():
    print(f"\n🔄 RESETTING AUTO-INCREMENT COUNTERS...")
    
    with connection.cursor() as cursor:
        # Get all tables
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            try:
                # Reset auto-increment to 1
                cursor.execute(f"ALTER TABLE `{table_name}` AUTO_INCREMENT = 1;")
                print(f"   ✅ Reset auto-increment for {table_name}")
            except Exception as e:
                # Some tables might not have auto-increment
                pass

def create_fresh_test_data():
    print(f"\n🌱 CREATING FRESH TEST DATA...")
    
    # Import models after database is clean
    from farm2market_backend.coreF2M.models import (
        CustomUser, FarmerProfile, BuyerProfile, Category, 
        FarmerListing, ProductCategory, Reservation
    )
    from decimal import Decimal
    
    try:
        # Create categories
        vegetables = Category.objects.create(name='Vegetables')
        fruits = Category.objects.create(name='Fruits')
        print(f"✅ Created categories")
        
        # Create admin
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
        
        # Create farmer
        farmer = CustomUser.objects.create_user(
            email='farmer@agriport.com',
            username='farmer',
            password='farmer123',
            first_name='John',
            last_name='Farmer',
            user_type='Farmer',
            is_active=True,
            is_approved=True
        )
        
        FarmerProfile.objects.create(
            farmer=farmer,
            location='Bamenda, Cameroon'
        )
        print(f"✅ Created farmer: {farmer.email}")
        
        # Create buyer
        buyer = CustomUser.objects.create_user(
            email='buyer@agriport.com',
            username='buyer',
            password='buyer123',
            first_name='Jane',
            last_name='Buyer',
            user_type='Buyer',
            is_active=True,
            is_approved=True
        )
        
        BuyerProfile.objects.create(
            buyer=buyer,
            location='Yaoundé, Cameroon'
        )
        print(f"✅ Created buyer: {buyer.email}")
        
        # Create products
        tomatoes = FarmerListing.objects.create(
            farmer=farmer,
            product_name='Fresh Tomatoes',
            price=Decimal('800.00'),
            quantity=50,
            quantity_unit='kg',
            description='Fresh organic tomatoes'
        )
        
        ProductCategory.objects.create(listing=tomatoes, category=vegetables)
        print(f"✅ Created product: {tomatoes.product_name}")
        
        # Create reservation
        Reservation.objects.create(
            buyer=buyer,
            listing=tomatoes,
            quantity=10,
            unit_price=tomatoes.price,
            total_amount=tomatoes.price * 10,
            delivery_method='delivery',
            delivery_address='Test Address, Cameroon',
            status='pending',
            buyer_notes='Test reservation'
        )
        print(f"✅ Created reservation: {buyer.first_name} -> {tomatoes.product_name}")
        
        print(f"\n🎉 Fresh test data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")

if __name__ == '__main__':
    print("🔥 COMPLETE MySQL DATABASE CLEANUP")
    print("=" * 60)
    
    # Clean everything completely
    clean_mysql_database_completely()
    
    # Reset auto-increment counters
    reset_auto_increment_counters()
    
    # Create fresh test data
    create_fresh_test_data()
    
    print(f"\n" + "=" * 60)
    print(f"✅ COMPLETE MySQL DATABASE CLEANUP FINISHED!")
    print(f"🔑 CLEAN CREDENTIALS:")
    print(f"   👑 Admin: admin@agriport.com / admin123")
    print(f"   🌱 Farmer: farmer@agriport.com / farmer123")
    print(f"   🛒 Buyer: buyer@agriport.com / buyer123")
    print(f"🚀 DATABASE IS 100% CLEAN AND READY!")
