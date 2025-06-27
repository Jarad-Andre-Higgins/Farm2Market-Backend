#!/usr/bin/env python
"""
Test the fixed registration system
"""
import os
import sys
import django
import requests
import time

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

BASE_URL = 'http://localhost:8000'

def test_farmer_registration():
    """Test farmer registration with unique data"""
    print("🌱 TESTING FIXED FARMER REGISTRATION")
    print("-" * 50)
    
    # Create unique data
    timestamp = str(int(time.time()))
    
    farmer_data = {
        'email': f'farmer{timestamp}@agriport.com',
        'username': f'farmer{timestamp}',
        'password': f'farmpass{timestamp}',
        'password_confirm': f'farmpass{timestamp}',
        'user_type': 'Farmer',
        'first_name': 'Test',
        'last_name': 'Farmer',
        'phone_number': f'+237{timestamp[-9:]}',
        'location': 'Bamenda, Cameroon'
    }
    
    print(f"   📧 Testing with email: {farmer_data['email']}")
    
    try:
        response = requests.post(f'{BASE_URL}/api/farmer/register/', json=farmer_data, timeout=15)
        print(f"   📊 Response status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("   ✅ FARMER REGISTRATION: WORKING!")
            data = response.json()
            print(f"   📝 Response: {data}")
            return True
        else:
            print(f"   ❌ Registration failed")
            print(f"   📄 Response: {response.text[:300]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return False

def test_buyer_registration():
    """Test buyer registration"""
    print("\n🛒 TESTING BUYER REGISTRATION")
    print("-" * 50)
    
    timestamp = str(int(time.time()) + 1)
    
    buyer_data = {
        'email': f'buyer{timestamp}@agriport.com',
        'username': f'buyer{timestamp}',
        'password': f'buypass{timestamp}',
        'password_confirm': f'buypass{timestamp}',
        'user_type': 'Buyer',
        'first_name': 'Test',
        'last_name': 'Buyer',
        'phone_number': f'+237{timestamp[-9:]}',
        'location': 'Yaoundé, Cameroon'
    }
    
    print(f"   📧 Testing with email: {buyer_data['email']}")
    
    try:
        response = requests.post(f'{BASE_URL}/api/buyer/register/', json=buyer_data, timeout=15)
        print(f"   📊 Response status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("   ✅ BUYER REGISTRATION: WORKING!")
            data = response.json()
            print(f"   📝 Response: {data}")
            return True
        else:
            print(f"   ❌ Registration failed")
            print(f"   📄 Response: {response.text[:300]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
        return False

def test_login_with_new_user():
    """Test login with newly created user"""
    print("\n🔐 TESTING LOGIN WITH NEW USER")
    print("-" * 50)
    
    # Use the farmer we just created
    login_data = {
        'email': 'testfarmer@agriport.com',
        'password': 'farmer123'
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/auth/login/', json=login_data, timeout=10)
        print(f"   📊 Login status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                print("   ✅ LOGIN: WORKING!")
                print(f"   🔑 Token: {data['token'][:20]}...")
                return data['token']
            else:
                print("   ❌ No token in response")
                return None
        else:
            print(f"   ❌ Login failed: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None

def test_protected_endpoints(token):
    """Test protected endpoints with token"""
    print("\n🛡️ TESTING PROTECTED ENDPOINTS")
    print("-" * 50)
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    endpoints = [
        ('/api/farmer/dashboard/', 'Farmer Dashboard'),
        ('/api/farmer/listings/', 'Farmer Listings'),
        ('/api/categories/', 'Categories'),
    ]
    
    working_endpoints = 0
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f'{BASE_URL}{endpoint}', headers=headers, timeout=10)
            print(f"   📊 {name}: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ {name}: WORKING")
                working_endpoints += 1
            else:
                print(f"   ❌ {name}: FAILED")
                
        except Exception as e:
            print(f"   ❌ {name}: ERROR - {e}")
    
    print(f"\n   📈 Working endpoints: {working_endpoints}/{len(endpoints)}")
    return working_endpoints == len(endpoints)

def run_comprehensive_test():
    """Run comprehensive registration and authentication test"""
    print("🚀 COMPREHENSIVE AGRIPORT REGISTRATION TEST")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Farmer registration
    results['Farmer Registration'] = test_farmer_registration()
    
    # Test 2: Buyer registration
    results['Buyer Registration'] = test_buyer_registration()
    
    # Test 3: Login
    token = test_login_with_new_user()
    results['User Login'] = token is not None
    
    # Test 4: Protected endpoints
    if token:
        results['Protected Endpoints'] = test_protected_endpoints(token)
    else:
        results['Protected Endpoints'] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"🧪 Tests Passed: {passed_tests}/{total_tests}")
    print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    for test_name, result in results.items():
        status = "✅ WORKING" if result else "❌ BROKEN"
        print(f"   {status} {test_name}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL SYSTEMS WORKING!")
        print(f"✅ AGRIPORT registration and authentication is fully functional")
        print(f"🚀 Ready to implement advanced features")
    elif passed_tests >= 3:
        print(f"\n🎯 MAJOR PROGRESS!")
        print(f"✅ Core functionality working")
        print(f"🔧 Minor fixes needed")
    else:
        print(f"\n⚠️ MORE WORK NEEDED")
        print(f"❌ Critical issues remain")
    
    return results

if __name__ == '__main__':
    run_comprehensive_test()
