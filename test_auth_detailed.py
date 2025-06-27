#!/usr/bin/env python
"""
Detailed authentication testing for Farm2Market APIs
"""
import requests
import json

def test_buyer_auth():
    """Test buyer authentication in detail"""
    base_url = "http://localhost:8000/api"
    
    print("🔐 DETAILED BUYER AUTHENTICATION TEST")
    print("=" * 50)
    
    # Test 1: Buyer Registration
    print("\n1. Testing Buyer Registration...")
    registration_data = {
        "username": "testbuyer2",
        "email": "testbuyer2@example.com",
        "first_name": "Test",
        "last_name": "Buyer2"
    }
    
    try:
        response = requests.post(f"{base_url}/buyer/register/", json=registration_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Registration successful!")
            print(f"Generated password: {data.get('password', 'Not provided')}")
        else:
            print(f"❌ Registration failed")
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    # Test 2: Buyer Login with existing user
    print("\n2. Testing Buyer Login with existing user...")
    login_data = {
        "email": "testbuyer@buyer.com",
        "password": "buyer123"
    }
    
    try:
        response = requests.post(f"{base_url}/buyer/login/", json=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('token'):
                token = data['token']
                print(f"✅ Login successful!")
                print(f"Token: {token[:50]}...")
                
                # Test 3: Use token for protected endpoint
                print("\n3. Testing protected endpoint with token...")
                headers = {'Authorization': f'Token {token}'}
                
                profile_response = requests.get(f"{base_url}/buyer/profile/", headers=headers)
                print(f"Profile Status Code: {profile_response.status_code}")
                print(f"Profile Response: {profile_response.text}")
                
            else:
                print(f"❌ Login failed - no token in response")
        else:
            print(f"❌ Login failed")
            
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    # Test 4: Test categories endpoint
    print("\n4. Testing Categories endpoint...")
    try:
        response = requests.get(f"{base_url}/categories/")
        print(f"Categories Status Code: {response.status_code}")
        print(f"Categories Response: {response.text}")
    except Exception as e:
        print(f"❌ Categories error: {e}")
    
    # Test 5: Test farmer listings
    print("\n5. Testing Farmer Listings...")
    try:
        response = requests.get(f"{base_url}/farmer/1/listings/")
        print(f"Farmer Listings Status Code: {response.status_code}")
        print(f"Farmer Listings Response: {response.text}")
    except Exception as e:
        print(f"❌ Farmer Listings error: {e}")

if __name__ == '__main__':
    test_buyer_auth()
