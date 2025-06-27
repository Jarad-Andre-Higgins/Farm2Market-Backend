#!/usr/bin/env python
"""
DEEP FUNCTIONALITY TEST - Test actual user workflows and features
"""
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import CustomUser, FarmerListing, Reservation

BASE_URL = 'http://localhost:8000'

def test_user_registration():
    """Test if user registration actually works"""
    print("👤 TESTING USER REGISTRATION")
    print("-" * 40)
    
    # Test farmer registration
    farmer_data = {
        'email': 'testfarmer@test.com',
        'username': 'testfarmer',
        'password': 'testpass123',
        'password_confirm': 'testpass123',
        'user_type': 'Farmer',
        'first_name': 'Test',
        'last_name': 'Farmer',
        'phone_number': '+237123456789'
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/farmer/register/', json=farmer_data)
        if response.status_code == 201:
            print("   ✅ Farmer registration: WORKING")
            return True
        else:
            print(f"   ❌ Farmer registration: FAILED - {response.status_code}")
            print(f"      Response: {response.text[:100]}...")
            return False
    except Exception as e:
        print(f"   ❌ Farmer registration: ERROR - {e}")
        return False

def test_user_login():
    """Test if login actually works with real users"""
    print("\n🔐 TESTING USER LOGIN")
    print("-" * 40)
    
    # Get a real user from database
    try:
        user = CustomUser.objects.first()
        if not user:
            print("   ❌ No users in database to test login")
            return False
        
        login_data = {
            'email': user.email,
            'password': 'admin123'  # Try common password
        }
        
        response = requests.post(f'{BASE_URL}/api/auth/login/', json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                print("   ✅ Login with token: WORKING")
                return True
            else:
                print("   ⚠️  Login responds but no token")
                return False
        else:
            print(f"   ❌ Login: FAILED - {response.status_code}")
            print(f"      Response: {response.text[:100]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Login test: ERROR - {e}")
        return False

def test_farmer_dashboard_data():
    """Test if farmer dashboard actually loads real data"""
    print("\n🌱 TESTING FARMER DASHBOARD DATA")
    print("-" * 40)
    
    try:
        # First login to get token
        user = CustomUser.objects.filter(user_type='Farmer').first()
        if not user:
            print("   ❌ No farmer users to test dashboard")
            return False
        
        # Try to get dashboard data
        response = requests.get(f'{BASE_URL}/api/farmer/dashboard/')
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Dashboard data loaded: {len(data)} items")
            
            # Check if it has real data structure
            if isinstance(data, dict) and 'listings' in data:
                print("   ✅ Dashboard has listings data")
                return True
            else:
                print("   ⚠️  Dashboard responds but data structure unclear")
                return False
        else:
            print(f"   ❌ Dashboard data: FAILED - {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Dashboard test: ERROR - {e}")
        return False

def test_product_listing_creation():
    """Test if farmers can actually create product listings"""
    print("\n📦 TESTING PRODUCT LISTING CREATION")
    print("-" * 40)
    
    try:
        farmer = CustomUser.objects.filter(user_type='Farmer').first()
        if not farmer:
            print("   ❌ No farmer to test listing creation")
            return False
        
        listing_data = {
            'product_name': 'Test Tomatoes',
            'description': 'Fresh test tomatoes',
            'price': '500.00',
            'quantity': 10,
            'quantity_unit': 'kg'
        }
        
        response = requests.post(f'{BASE_URL}/api/farmer/listings/', json=listing_data)
        
        if response.status_code in [200, 201]:
            print("   ✅ Product listing creation: WORKING")
            return True
        else:
            print(f"   ❌ Product listing: FAILED - {response.status_code}")
            print(f"      Response: {response.text[:100]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Listing creation test: ERROR - {e}")
        return False

def test_buyer_product_browsing():
    """Test if buyers can browse products"""
    print("\n🛒 TESTING BUYER PRODUCT BROWSING")
    print("-" * 40)
    
    try:
        response = requests.get(f'{BASE_URL}/api/products/')
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"   ✅ Product browsing: WORKING - {len(data)} products")
                return True
            else:
                print("   ⚠️  Product browsing responds but no products")
                return False
        else:
            print(f"   ❌ Product browsing: FAILED - {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Product browsing test: ERROR - {e}")
        return False

def test_reservation_system():
    """Test if reservation system works"""
    print("\n📋 TESTING RESERVATION SYSTEM")
    print("-" * 40)
    
    try:
        # Check if there are listings to reserve
        listing = FarmerListing.objects.first()
        buyer = CustomUser.objects.filter(user_type='Buyer').first()
        
        if not listing or not buyer:
            print("   ❌ No listing or buyer to test reservations")
            return False
        
        reservation_data = {
            'listing_id': listing.listing_id,
            'quantity': 2,
            'delivery_method': 'pickup',
            'buyer_notes': 'Test reservation'
        }
        
        response = requests.post(f'{BASE_URL}/api/reservations/', json=reservation_data)
        
        if response.status_code in [200, 201]:
            print("   ✅ Reservation creation: WORKING")
            return True
        else:
            print(f"   ❌ Reservation: FAILED - {response.status_code}")
            print(f"      Response: {response.text[:100]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Reservation test: ERROR - {e}")
        return False

def test_frontend_backend_integration():
    """Test if frontend can actually connect to backend"""
    print("\n🔗 TESTING FRONTEND-BACKEND INTEGRATION")
    print("-" * 40)
    
    try:
        # Test CORS and basic connectivity
        response = requests.options(f'{BASE_URL}/api/', headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET'
        })
        
        if response.status_code in [200, 204]:
            print("   ✅ CORS configuration: WORKING")
        else:
            print("   ⚠️  CORS may have issues")
        
        # Test if API returns JSON
        response = requests.get(f'{BASE_URL}/api/')
        if response.headers.get('content-type', '').startswith('application/json'):
            print("   ✅ JSON API responses: WORKING")
            return True
        else:
            print("   ❌ API not returning JSON")
            return False
            
    except Exception as e:
        print(f"   ❌ Integration test: ERROR - {e}")
        return False

def test_database_data_integrity():
    """Test if database has consistent, real data"""
    print("\n🗄️ TESTING DATABASE DATA INTEGRITY")
    print("-" * 40)
    
    try:
        # Check user data
        users = CustomUser.objects.all()
        farmers = users.filter(user_type='Farmer')
        buyers = users.filter(user_type='Buyer')
        admins = users.filter(user_type='Admin')
        
        print(f"   📊 Total users: {users.count()}")
        print(f"   🌱 Farmers: {farmers.count()}")
        print(f"   🛒 Buyers: {buyers.count()}")
        print(f"   👑 Admins: {admins.count()}")
        
        # Check if users have proper data
        real_users = 0
        for user in users:
            if user.email and user.first_name and user.last_name:
                real_users += 1
        
        print(f"   ✅ Users with complete data: {real_users}/{users.count()}")
        
        # Check listings
        listings = FarmerListing.objects.all()
        print(f"   📦 Product listings: {listings.count()}")
        
        # Check reservations
        reservations = Reservation.objects.all()
        print(f"   📋 Reservations: {reservations.count()}")
        
        if users.count() > 0 and real_users > 0:
            print("   ✅ Database has real data")
            return True
        else:
            print("   ❌ Database lacks proper data")
            return False
            
    except Exception as e:
        print(f"   ❌ Database integrity test: ERROR - {e}")
        return False

def generate_deep_report(results):
    """Generate detailed functionality report"""
    print("\n" + "=" * 60)
    print("📋 DEEP FUNCTIONALITY REPORT")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"🧪 Functional Tests Passed: {passed_tests}/{total_tests}")
    print(f"📊 Functionality Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n🔍 DETAILED FUNCTIONALITY:")
    for test_name, result in results.items():
        status = "✅ WORKING" if result else "❌ BROKEN"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 HONEST ASSESSMENT:")
    if passed_tests >= total_tests * 0.8:
        print(f"✅ CORE FUNCTIONALITY IS WORKING")
        print(f"🎉 Project has solid foundation")
    elif passed_tests >= total_tests * 0.5:
        print(f"⚠️  PARTIAL FUNCTIONALITY")
        print(f"🔧 Some features work, others need fixing")
    else:
        print(f"❌ MAJOR FUNCTIONALITY ISSUES")
        print(f"🚨 Most features are broken or incomplete")
    
    print(f"\n📋 WHAT ACTUALLY WORKS:")
    working_features = [name for name, result in results.items() if result]
    for feature in working_features:
        print(f"   ✅ {feature}")
    
    print(f"\n🔧 WHAT NEEDS FIXING:")
    broken_features = [name for name, result in results.items() if not result]
    for feature in broken_features:
        print(f"   ❌ {feature}")

if __name__ == '__main__':
    print("🔍 DEEP FUNCTIONALITY TEST")
    print("=" * 60)
    print("Testing actual user workflows and features...")
    
    # Run deep functionality tests
    results = {}
    results['User Registration'] = test_user_registration()
    results['User Login'] = test_user_login()
    results['Farmer Dashboard'] = test_farmer_dashboard_data()
    results['Product Listing'] = test_product_listing_creation()
    results['Product Browsing'] = test_buyer_product_browsing()
    results['Reservation System'] = test_reservation_system()
    results['Frontend Integration'] = test_frontend_backend_integration()
    results['Database Integrity'] = test_database_data_integrity()
    
    # Generate detailed report
    generate_deep_report(results)
