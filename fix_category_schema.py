#!/usr/bin/env python
"""
Manually fix category schema
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

def fix_category_schema():
    """Manually update category table schema"""
    print("🔧 FIXING CATEGORY SCHEMA")
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
        # Check current category table structure
        cursor.execute("DESCRIBE categories")
        current_columns = [row[0] for row in cursor.fetchall()]
        print(f"   📋 Current columns: {current_columns}")
        
        # Add missing columns if they don't exist
        new_columns = [
            ("description", "ALTER TABLE categories ADD COLUMN description TEXT"),
            ("created_by_id", "ALTER TABLE categories ADD COLUMN created_by_id INT"),
            ("approval_status", "ALTER TABLE categories ADD COLUMN approval_status VARCHAR(20) DEFAULT 'approved'"),
            ("approved_by_id", "ALTER TABLE categories ADD COLUMN approved_by_id INT NULL"),
            ("approved_at", "ALTER TABLE categories ADD COLUMN approved_at DATETIME NULL"),
            ("created_at", "ALTER TABLE categories ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "ALTER TABLE categories ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        ]
        
        for column_name, sql in new_columns:
            if column_name not in current_columns:
                try:
                    cursor.execute(sql)
                    print(f"   ✅ Added column: {column_name}")
                except Exception as e:
                    print(f"   ⚠️  Column {column_name}: {e}")
        
        # Set default values for existing categories
        print("\n   🔄 Setting default values...")
        
        # Get the first farmer user to assign as creator
        cursor.execute("SELECT id FROM coreF2M_customuser WHERE user_type='Farmer' LIMIT 1")
        farmer_result = cursor.fetchone()
        if farmer_result:
            farmer_id = farmer_result[0]
            cursor.execute(f"UPDATE categories SET created_by_id = {farmer_id} WHERE created_by_id IS NULL")
            print(f"   ✅ Set default creator to farmer ID: {farmer_id}")
        
        # Set approval status to approved for existing categories
        cursor.execute("UPDATE categories SET approval_status = 'approved' WHERE approval_status IS NULL")
        print("   ✅ Set existing categories to approved")
        
        # Add foreign key constraints
        try:
            cursor.execute("""
                ALTER TABLE categories 
                ADD CONSTRAINT fk_category_created_by 
                FOREIGN KEY (created_by_id) REFERENCES coreF2M_customuser(id)
            """)
            print("   ✅ Added created_by foreign key")
        except Exception as e:
            print(f"   ⚠️  Foreign key constraint: {e}")
        
        try:
            cursor.execute("""
                ALTER TABLE categories 
                ADD CONSTRAINT fk_category_approved_by 
                FOREIGN KEY (approved_by_id) REFERENCES coreF2M_customuser(id)
            """)
            print("   ✅ Added approved_by foreign key")
        except Exception as e:
            print(f"   ⚠️  Foreign key constraint: {e}")
        
        # Add indexes
        indexes = [
            ("idx_category_approval", "CREATE INDEX idx_category_approval ON categories(approval_status)"),
            ("idx_category_creator", "CREATE INDEX idx_category_creator ON categories(created_by_id, approval_status)")
        ]
        
        for index_name, sql in indexes:
            try:
                cursor.execute(sql)
                print(f"   ✅ Added index: {index_name}")
            except Exception as e:
                print(f"   ⚠️  Index {index_name}: {e}")
        
        connection.commit()
        print("\n   🎉 Category schema updated successfully!")
        
        # Verify the changes
        cursor.execute("DESCRIBE categories")
        updated_columns = [row[0] for row in cursor.fetchall()]
        print(f"   📋 Updated columns: {updated_columns}")
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        print(f"   📊 Total categories: {count}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        connection.rollback()
    
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    fix_category_schema()
