#!/usr/bin/env python
"""
Test the general authentication endpoints that frontend expects
"""
import requests
import json

def test_general_auth():
    """Test general authentication endpoints"""
    base_url = "http://localhost:8000/api"
    
    print("🔐 TESTING GENERAL AUTHENTICATION ENDPOINTS")
    print("=" * 50)
    
    # Test 1: General Login (should work for both farmers and buyers)
    print("\n1. Testing General Login with buyer credentials...")
    login_data = {
        "email": "testbuyer@buyer.com",
        "password": "buyer123"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login/", json=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('token'):
                token = data['token']
                print(f"✅ General login successful!")
                print(f"Token: {token[:50]}...")
                print(f"User Type: {data.get('user', {}).get('user_type')}")
                
                # Test protected endpoint with this token
                print("\n2. Testing protected endpoint with general auth token...")
                headers = {'Authorization': f'Token {token}'}
                
                profile_response = requests.get(f"{base_url}/buyer/profile/", headers=headers)
                print(f"Profile Status Code: {profile_response.status_code}")
                print(f"Profile Response: {profile_response.text}")
                
                if profile_response.status_code == 200:
                    print(f"✅ Protected endpoint works with general auth token!")
                else:
                    print(f"❌ Protected endpoint failed")
                
            else:
                print(f"❌ General login failed - no token in response")
        else:
            print(f"❌ General login failed")
            
    except Exception as e:
        print(f"❌ General login error: {e}")
    
    # Test 2: General Login with farmer credentials
    print("\n3. Testing General Login with farmer credentials...")
    farmer_login_data = {
        "email": "testfarmer@farm.com",
        "password": "farmer123"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login/", json=farmer_login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('token'):
                farmer_token = data['token']
                print(f"✅ Farmer general login successful!")
                print(f"Token: {farmer_token[:50]}...")
                print(f"User Type: {data.get('user', {}).get('user_type')}")
                
                # Test farmer endpoint
                print("\n4. Testing farmer endpoint with general auth token...")
                headers = {'Authorization': f'Token {farmer_token}'}
                
                farmer_response = requests.get(f"{base_url}/farmer/profile/", headers=headers)
                print(f"Farmer Profile Status Code: {farmer_response.status_code}")
                print(f"Farmer Profile Response: {farmer_response.text}")
                
                if farmer_response.status_code == 200:
                    print(f"✅ Farmer endpoint works with general auth token!")
                else:
                    print(f"❌ Farmer endpoint failed")
                
            else:
                print(f"❌ Farmer general login failed - no token in response")
        else:
            print(f"❌ Farmer general login failed")
            
    except Exception as e:
        print(f"❌ Farmer general login error: {e}")
    
    # Test 3: Test notifications endpoint
    print("\n5. Testing notifications endpoint...")
    try:
        # Use buyer token from earlier
        headers = {'Authorization': f'Token {token}'}
        response = requests.get(f"{base_url}/notifications/", headers=headers)
        print(f"Notifications Status Code: {response.status_code}")
        print(f"Notifications Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            notifications = data.get('notifications', [])
            print(f"✅ Notifications endpoint works! Found {len(notifications)} notifications")
        else:
            print(f"❌ Notifications endpoint failed")
    except Exception as e:
        print(f"❌ Notifications error: {e}")
    
    print("\n🎉 General authentication testing completed!")

if __name__ == '__main__':
    test_general_auth()
