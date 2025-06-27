#!/usr/bin/env python
"""
FINAL 4-HOUR TEST - Check what's working now
"""
import os
import sys
import django
import requests

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

BASE_URL = 'http://localhost:8000'

def test_farmer_login():
    """Test farmer login with created user"""
    print("🔐 TESTING FARMER LOGIN")
    print("-" * 40)
    
    login_data = {
        'email': 'testfarmer@agriport.com',
        'password': 'farmer123'
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/auth/login/', json=login_data, timeout=5)
        print(f"   Login status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                print(f"   ✅ Farmer login: WORKING")
                return data['token']
            else:
                print(f"   ❌ No token in response")
                return None
        else:
            print(f"   ❌ Login failed: {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None

def test_farmer_dashboard(token):
    """Test farmer dashboard with token"""
    print("\n🌱 TESTING FARMER DASHBOARD")
    print("-" * 40)
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f'{BASE_URL}/api/farmer/dashboard/', headers=headers, timeout=5)
        print(f"   Dashboard status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Farmer dashboard: WORKING")
            print(f"   📊 Data keys: {list(data.keys())}")
            return True
        else:
            print(f"   ❌ Dashboard failed: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Dashboard error: {e}")
        return False

def test_product_browsing():
    """Test product browsing"""
    print("\n📦 TESTING PRODUCT BROWSING")
    print("-" * 40)
    
    try:
        response = requests.get(f'{BASE_URL}/api/products/', timeout=5)
        print(f"   Products status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'products' in data:
                products = data['products']
                print(f"   ✅ Product browsing: WORKING - {len(products)} products")
                return True
            else:
                print(f"   ❌ Wrong format: {type(data)}")
                return False
        else:
            print(f"   ❌ Products failed: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Products error: {e}")
        return False

def test_registration():
    """Test registration with unique data"""
    print("\n👤 TESTING REGISTRATION")
    print("-" * 40)
    
    import time
    unique_id = str(int(time.time()))
    
    farmer_data = {
        'email': f'farmer{unique_id}@test.com',
        'username': f'farmer{unique_id}',
        'password': f'pass{unique_id}',
        'password_confirm': f'pass{unique_id}',
        'user_type': 'Farmer',
        'first_name': 'Test',
        'last_name': 'Farmer',
        'phone_number': f'+237{unique_id}',
        'location': 'Test Location'
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/farmer/register/', json=farmer_data, timeout=10)
        print(f"   Registration status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print(f"   ✅ Registration: WORKING")
            return True
        else:
            print(f"   ❌ Registration failed: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return False

def run_final_test():
    """Run final comprehensive test"""
    print("🚀 FINAL 4-HOUR FIX TEST")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Farmer login
    token = test_farmer_login()
    results['Farmer Login'] = token is not None
    
    # Test 2: Farmer dashboard (if login works)
    if token:
        results['Farmer Dashboard'] = test_farmer_dashboard(token)
    else:
        results['Farmer Dashboard'] = False
    
    # Test 3: Product browsing
    results['Product Browsing'] = test_product_browsing()
    
    # Test 4: Registration
    results['Registration'] = test_registration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 FINAL TEST RESULTS")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"🧪 Tests Passed: {passed_tests}/{total_tests}")
    print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    for test_name, result in results.items():
        status = "✅ WORKING" if result else "❌ BROKEN"
        print(f"   {status} {test_name}")
    
    if passed_tests >= 3:
        print(f"\n🎉 MAJOR PROGRESS MADE!")
        print(f"✅ Core functionality is working")
        print(f"🚀 Ready for frontend integration")
    else:
        print(f"\n⚠️  STILL NEEDS WORK")
        print(f"❌ More fixes required")
    
    # Next steps
    print(f"\n🎯 NEXT STEPS:")
    if not results['Farmer Login']:
        print("   1. Fix farmer login authentication")
    if not results['Farmer Dashboard']:
        print("   2. Fix farmer dashboard data loading")
    if not results['Product Browsing']:
        print("   3. Fix product browsing API")
    if not results['Registration']:
        print("   4. Fix registration system")
    
    if passed_tests == total_tests:
        print("   🎉 ALL SYSTEMS WORKING - READY FOR FRONTEND!")
    
    return results

if __name__ == '__main__':
    run_final_test()
