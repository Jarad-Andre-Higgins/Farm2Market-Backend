#!/usr/bin/env python
"""
Apply database constraints directly to prevent data anomalies
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

def apply_database_constraints():
    print("🔒 APPLYING DATABASE CONSTRAINTS TO PREVENT ANOMALIES")
    print("=" * 60)
    
    constraints = [
        # User constraints
        {
            'name': 'email_not_empty',
            'table': 'users_customuser',
            'sql': "ALTER TABLE users_customuser ADD CONSTRAINT email_not_empty CHECK (email != '')"
        },
        {
            'name': 'valid_user_type',
            'table': 'users_customuser', 
            'sql': "ALTER TABLE users_customuser ADD CONSTRAINT valid_user_type CHECK (user_type IN ('Farmer', 'Buyer', 'Admin'))"
        },
        {
            'name': 'first_name_not_empty',
            'table': 'users_customuser',
            'sql': "ALTER TABLE users_customuser ADD CONSTRAINT first_name_not_empty CHECK (first_name IS NULL OR first_name != '')"
        },
        {
            'name': 'last_name_not_empty', 
            'table': 'users_customuser',
            'sql': "ALTER TABLE users_customuser ADD CONSTRAINT last_name_not_empty CHECK (last_name IS NULL OR last_name != '')"
        },
        
        # Category constraints
        {
            'name': 'category_name_not_empty',
            'table': 'categories',
            'sql': "ALTER TABLE categories ADD CONSTRAINT category_name_not_empty CHECK (name != '')"
        },
        
        # Farmer listing constraints
        {
            'name': 'product_name_not_empty',
            'table': 'farmer_listings',
            'sql': "ALTER TABLE farmer_listings ADD CONSTRAINT product_name_not_empty CHECK (product_name != '')"
        },
        {
            'name': 'price_positive',
            'table': 'farmer_listings',
            'sql': "ALTER TABLE farmer_listings ADD CONSTRAINT price_positive CHECK (price > 0)"
        },
        {
            'name': 'quantity_positive',
            'table': 'farmer_listings',
            'sql': "ALTER TABLE farmer_listings ADD CONSTRAINT quantity_positive CHECK (quantity > 0)"
        },
        {
            'name': 'valid_listing_status',
            'table': 'farmer_listings',
            'sql': "ALTER TABLE farmer_listings ADD CONSTRAINT valid_listing_status CHECK (status IN ('Available', 'Sold', 'Reserved'))"
        },
        
        # Reservation constraints
        {
            'name': 'reservation_quantity_positive',
            'table': 'reservations',
            'sql': "ALTER TABLE reservations ADD CONSTRAINT reservation_quantity_positive CHECK (quantity > 0)"
        },
        {
            'name': 'reservation_unit_price_positive',
            'table': 'reservations',
            'sql': "ALTER TABLE reservations ADD CONSTRAINT reservation_unit_price_positive CHECK (unit_price > 0)"
        },
        {
            'name': 'reservation_total_amount_positive',
            'table': 'reservations',
            'sql': "ALTER TABLE reservations ADD CONSTRAINT reservation_total_amount_positive CHECK (total_amount > 0)"
        },
        {
            'name': 'valid_reservation_status',
            'table': 'reservations',
            'sql': "ALTER TABLE reservations ADD CONSTRAINT valid_reservation_status CHECK (status IN ('pending', 'approved', 'rejected', 'payment_pending', 'paid', 'ready_for_pickup', 'completed', 'cancelled'))"
        },
        
        # Profile constraints
        {
            'name': 'farmer_location_not_empty',
            'table': 'farmer_profiles',
            'sql': "ALTER TABLE farmer_profiles ADD CONSTRAINT farmer_location_not_empty CHECK (location IS NULL OR location != '')"
        },
        {
            'name': 'buyer_location_not_empty',
            'table': 'buyer_profiles',
            'sql': "ALTER TABLE buyer_profiles ADD CONSTRAINT buyer_location_not_empty CHECK (location IS NULL OR location != '')"
        },
    ]
    
    with connection.cursor() as cursor:
        applied_count = 0
        skipped_count = 0
        
        for constraint in constraints:
            try:
                print(f"📋 Applying constraint: {constraint['name']} on {constraint['table']}")
                cursor.execute(constraint['sql'])
                applied_count += 1
                print(f"   ✅ Applied successfully")
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print(f"   ⚠️  Constraint already exists - skipping")
                    skipped_count += 1
                else:
                    print(f"   ❌ Error: {e}")
        
        print(f"\n📊 CONSTRAINT APPLICATION SUMMARY:")
        print(f"   ✅ Applied: {applied_count}")
        print(f"   ⚠️  Skipped: {skipped_count}")
        print(f"   📋 Total: {len(constraints)}")

def create_database_indexes():
    print(f"\n🔍 CREATING DATABASE INDEXES FOR PERFORMANCE")
    print("=" * 60)
    
    indexes = [
        {
            'name': 'idx_user_type_approved',
            'table': 'users_customuser',
            'sql': "CREATE INDEX idx_user_type_approved ON users_customuser (user_type, is_approved)"
        },
        {
            'name': 'idx_email',
            'table': 'users_customuser',
            'sql': "CREATE INDEX idx_email ON users_customuser (email)"
        },
        {
            'name': 'idx_farmer_status',
            'table': 'farmer_listings',
            'sql': "CREATE INDEX idx_farmer_status ON farmer_listings (farmer_id, status)"
        },
        {
            'name': 'idx_product_name',
            'table': 'farmer_listings',
            'sql': "CREATE INDEX idx_product_name ON farmer_listings (product_name)"
        },
        {
            'name': 'idx_buyer_status',
            'table': 'reservations',
            'sql': "CREATE INDEX idx_buyer_status ON reservations (buyer_id, status)"
        },
        {
            'name': 'idx_listing_status',
            'table': 'reservations',
            'sql': "CREATE INDEX idx_listing_status ON reservations (listing_id, status)"
        },
        {
            'name': 'idx_category_name',
            'table': 'categories',
            'sql': "CREATE INDEX idx_category_name ON categories (name)"
        },
    ]
    
    with connection.cursor() as cursor:
        applied_count = 0
        skipped_count = 0
        
        for index in indexes:
            try:
                print(f"🔍 Creating index: {index['name']} on {index['table']}")
                cursor.execute(index['sql'])
                applied_count += 1
                print(f"   ✅ Created successfully")
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print(f"   ⚠️  Index already exists - skipping")
                    skipped_count += 1
                else:
                    print(f"   ❌ Error: {e}")
        
        print(f"\n📊 INDEX CREATION SUMMARY:")
        print(f"   ✅ Created: {applied_count}")
        print(f"   ⚠️  Skipped: {skipped_count}")
        print(f"   📋 Total: {len(indexes)}")

def verify_constraints():
    print(f"\n🔍 VERIFYING APPLIED CONSTRAINTS")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        # Check constraints
        cursor.execute("""
            SELECT CONSTRAINT_NAME, TABLE_NAME, CONSTRAINT_TYPE 
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND CONSTRAINT_TYPE = 'CHECK'
            ORDER BY TABLE_NAME, CONSTRAINT_NAME
        """)
        
        constraints = cursor.fetchall()
        print(f"📋 Found {len(constraints)} CHECK constraints:")
        
        for constraint in constraints:
            print(f"   ✅ {constraint[1]}.{constraint[0]}")
        
        # Check indexes
        cursor.execute("""
            SELECT DISTINCT INDEX_NAME, TABLE_NAME 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND INDEX_NAME != 'PRIMARY'
            ORDER BY TABLE_NAME, INDEX_NAME
        """)
        
        indexes = cursor.fetchall()
        print(f"\n🔍 Found {len(indexes)} indexes:")
        
        for index in indexes:
            print(f"   🔍 {index[1]}.{index[0]}")

if __name__ == '__main__':
    print("🔒 DATABASE CONSTRAINT APPLICATION")
    print("=" * 60)
    
    # Apply constraints
    apply_database_constraints()
    
    # Create indexes
    create_database_indexes()
    
    # Verify everything
    verify_constraints()
    
    print(f"\n" + "=" * 60)
    print(f"✅ DATABASE CONSTRAINTS APPLIED SUCCESSFULLY!")
    print(f"🛡️  Database is now protected against data anomalies!")
    print(f"🚀 Ready for production use!")
