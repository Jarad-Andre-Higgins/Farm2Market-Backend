#!/usr/bin/env python
"""
HONEST SYSTEM TEST - Check what actually works vs what's broken
"""
import os
import sys
import django
import requests
from django.db import connection
from django.core.management import execute_from_command_line

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')

def test_django_setup():
    """Test if Django is properly configured"""
    print("🔧 TESTING DJANGO SETUP")
    print("-" * 40)
    
    try:
        django.setup()
        print("   ✅ Django setup: SUCCESS")
        return True
    except Exception as e:
        print(f"   ❌ Django setup: FAILED - {e}")
        return False

def test_database_connection():
    """Test database connectivity"""
    print("\n🗄️ TESTING DATABASE CONNECTION")
    print("-" * 40)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("   ✅ Database connection: SUCCESS")
            
            # Test if our tables exist
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            required_tables = [
                'users_customuser',
                'farmer_profiles', 
                'buyer_profiles',
                'categories',
                'farmer_listings',
                'reservations'
            ]
            
            missing_tables = []
            for table in required_tables:
                if table in table_names:
                    print(f"   ✅ Table {table}: EXISTS")
                else:
                    print(f"   ❌ Table {table}: MISSING")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"   ⚠️  Missing tables: {missing_tables}")
                return False
            else:
                print("   ✅ All required tables: EXIST")
                return True
                
    except Exception as e:
        print(f"   ❌ Database connection: FAILED - {e}")
        return False

def test_models():
    """Test if Django models work"""
    print("\n📊 TESTING DJANGO MODELS")
    print("-" * 40)
    
    try:
        from farm2market_backend.coreF2M.models import CustomUser, Category, FarmerListing
        
        # Test user count
        user_count = CustomUser.objects.count()
        print(f"   ✅ Users in database: {user_count}")
        
        # Test category count
        category_count = Category.objects.count()
        print(f"   ✅ Categories in database: {category_count}")
        
        # Test listing count
        listing_count = FarmerListing.objects.count()
        print(f"   ✅ Listings in database: {listing_count}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model testing: FAILED - {e}")
        return False

def test_django_server():
    """Test if Django development server can start"""
    print("\n🌐 TESTING DJANGO SERVER")
    print("-" * 40)
    
    try:
        # Try to make a request to the server
        response = requests.get('http://localhost:8000/', timeout=5)
        if response.status_code == 200:
            print("   ✅ Django server: RUNNING")
            return True
        else:
            print(f"   ⚠️  Django server: RESPONDING but status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Django server: NOT RUNNING")
        return False
    except Exception as e:
        print(f"   ❌ Django server test: FAILED - {e}")
        return False

def test_api_endpoints():
    """Test if API endpoints are working"""
    print("\n🔌 TESTING API ENDPOINTS")
    print("-" * 40)
    
    base_url = 'http://localhost:8000'
    endpoints = [
        '/api/',
        '/api/auth/login/',
        '/api/categories/',
        '/api/farmer/listings/',
    ]
    
    working_endpoints = 0
    total_endpoints = len(endpoints)
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 405]:  # 401/405 means endpoint exists
                print(f"   ✅ {endpoint}: WORKING")
                working_endpoints += 1
            else:
                print(f"   ❌ {endpoint}: ERROR {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: FAILED - {str(e)[:50]}...")
    
    print(f"   📊 Working endpoints: {working_endpoints}/{total_endpoints}")
    return working_endpoints == total_endpoints

def test_frontend_files():
    """Test if frontend files exist and are accessible"""
    print("\n🎨 TESTING FRONTEND FILES")
    print("-" * 40)
    
    frontend_path = "../Frontend"
    required_files = [
        "index.html",
        "Farmer/loginfarmer.html",
        "Farmer/farmer dashboard.html",
        "Buyer/loginbuyer.html",
        "Buyer/buyerdashboard.html",
        "Admin/adminlogin.html"
    ]
    
    existing_files = 0
    total_files = len(required_files)
    
    for file_path in required_files:
        full_path = os.path.join(frontend_path, file_path)
        if os.path.exists(full_path):
            print(f"   ✅ {file_path}: EXISTS")
            existing_files += 1
        else:
            print(f"   ❌ {file_path}: MISSING")
    
    print(f"   📊 Existing files: {existing_files}/{total_files}")
    return existing_files == total_files

def test_authentication():
    """Test if authentication system works"""
    print("\n🔐 TESTING AUTHENTICATION SYSTEM")
    print("-" * 40)
    
    try:
        # Test login endpoint
        login_data = {
            'email': 'admin@agriport.com',
            'password': 'admin123'
        }
        
        response = requests.post(
            'http://localhost:8000/api/auth/login/',
            json=login_data,
            timeout=5
        )
        
        if response.status_code == 200:
            print("   ✅ Login endpoint: WORKING")
            return True
        elif response.status_code == 400:
            print("   ⚠️  Login endpoint: WORKING but credentials invalid")
            return True
        else:
            print(f"   ❌ Login endpoint: ERROR {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Authentication test: FAILED - {e}")
        return False

def generate_status_report(results):
    """Generate final status report"""
    print("\n" + "=" * 60)
    print("📋 HONEST PROJECT STATUS REPORT")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"🧪 Tests Passed: {passed_tests}/{total_tests}")
    print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n🔍 DETAILED RESULTS:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL SYSTEMS OPERATIONAL")
        print(f"✅ Project is ready for development")
    elif passed_tests >= total_tests * 0.7:
        print(f"\n⚠️  MOSTLY WORKING - Some issues to fix")
        print(f"🔧 Project needs minor fixes")
    else:
        print(f"\n🚨 MAJOR ISSUES DETECTED")
        print(f"❌ Project needs significant work")
    
    print(f"\n🎯 NEXT STEPS:")
    if not results.get('Django Setup'):
        print("   1. Fix Django configuration")
    if not results.get('Database'):
        print("   2. Fix database connection and migrations")
    if not results.get('Django Server'):
        print("   3. Start Django development server")
    if not results.get('API Endpoints'):
        print("   4. Fix API endpoint issues")
    if not results.get('Frontend Files'):
        print("   5. Ensure all frontend files exist")
    if not results.get('Authentication'):
        print("   6. Fix authentication system")

if __name__ == '__main__':
    print("🔍 HONEST FARM2MARKET SYSTEM TEST")
    print("=" * 60)
    print("Testing what actually works vs what's broken...")
    
    # Run all tests
    results = {}
    results['Django Setup'] = test_django_setup()
    results['Database'] = test_database_connection()
    results['Models'] = test_models()
    results['Django Server'] = test_django_server()
    results['API Endpoints'] = test_api_endpoints()
    results['Frontend Files'] = test_frontend_files()
    results['Authentication'] = test_authentication()
    
    # Generate report
    generate_status_report(results)
