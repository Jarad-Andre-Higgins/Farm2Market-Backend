#!/usr/bin/env python
"""
Final fix for categories system
"""
import os
import sys
import django
import MySQLdb

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from django.conf import settings

def fix_categories_final():
    """Final fix for categories"""
    print("🔧 FINAL CATEGORY FIX")
    print("-" * 40)
    
    # Connect to MySQL
    db_config = settings.DATABASES['default']
    connection = MySQLdb.connect(
        host=db_config['HOST'],
        user=db_config['USER'],
        passwd=db_config['PASSWORD'],
        db=db_config['NAME'],
        port=int(db_config['PORT'])
    )
    
    cursor = connection.cursor()
    
    try:
        # Check current structure
        cursor.execute("DESCRIBE categories")
        columns = cursor.fetchall()
        print("   📋 Current columns:")
        for col in columns:
            print(f"      {col[0]} - {col[1]}")
        
        # Get farmer ID
        cursor.execute("SELECT id FROM coreF2M_customuser WHERE user_type='Farmer' LIMIT 1")
        farmer_result = cursor.fetchone()
        farmer_id = farmer_result[0] if farmer_result else 1
        
        # Update existing categories with proper values
        cursor.execute(f"""
            UPDATE categories 
            SET created_by_id = {farmer_id}, 
                approval_status = 'approved',
                created_at = NOW(),
                updated_at = NOW()
            WHERE created_by_id IS NULL
        """)
        
        print(f"   ✅ Updated existing categories with farmer ID: {farmer_id}")
        
        # Create some default approved categories
        default_categories = [
            ("Vegetables", "Fresh vegetables and greens"),
            ("Fruits", "Fresh fruits and berries"),
            ("Grains", "Rice, corn, wheat and other grains"),
            ("Legumes", "Beans, peas, lentils and legumes"),
            ("Tubers", "Potatoes, yams, cassava and root vegetables")
        ]
        
        for name, desc in default_categories:
            try:
                cursor.execute("""
                    INSERT INTO categories (name, description, created_by_id, approval_status, created_at, updated_at)
                    VALUES (%s, %s, %s, 'approved', NOW(), NOW())
                    ON DUPLICATE KEY UPDATE description = VALUES(description)
                """, (name, desc, farmer_id))
                print(f"   ✅ Added/Updated category: {name}")
            except Exception as e:
                print(f"   ⚠️  Category {name}: {e}")
        
        connection.commit()
        
        # Verify the fix
        cursor.execute("SELECT name, approval_status, created_by_id FROM categories")
        categories = cursor.fetchall()
        print(f"\n   📊 Total categories: {len(categories)}")
        for cat in categories:
            print(f"      - {cat[0]} ({cat[1]}) by user {cat[2]}")
        
        print("\n   🎉 Categories system fixed!")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        connection.rollback()
    
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    fix_categories_final()
