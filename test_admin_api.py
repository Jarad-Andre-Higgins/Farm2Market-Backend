#!/usr/bin/env python
"""
Test Admin API endpoints directly
"""
import requests
import json

def test_admin_login():
    """Test admin login API"""
    print("🔐 Testing Admin Login API...")
    
    url = "http://localhost:8000/api/admin/login/"
    data = {
        'email': 'admin@agriport.com',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                token = result.get('token')
                admin_info = result.get('admin', {})
                print(f"✅ Login successful!")
                print(f"Token: {token[:20]}...")
                print(f"Admin: {admin_info.get('username')} ({admin_info.get('email')})")
                return token
            else:
                print(f"❌ Login failed: {result.get('error')}")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_admin_dashboard(token):
    """Test admin dashboard API"""
    if not token:
        print("❌ No token available for dashboard test")
        return
        
    print("\n📊 Testing Admin Dashboard API...")
    
    url = "http://localhost:8000/api/admin/dashboard/"
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                dashboard_data = result.get('dashboard_data', {})
                system_stats = dashboard_data.get('system_stats', {})
                print(f"✅ Dashboard data retrieved!")
                print(f"Total Users: {system_stats.get('total_users')}")
                print(f"Total Farmers: {system_stats.get('total_farmers')}")
                print(f"Total Buyers: {system_stats.get('total_buyers')}")
                print(f"Pending Farmers: {system_stats.get('pending_farmers')}")
            else:
                print(f"❌ Dashboard failed: {result.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_create_admin(token):
    """Test create admin API"""
    if not token:
        print("❌ No token available for create admin test")
        return
        
    print("\n👤 Testing Create Admin API...")
    
    url = "http://localhost:8000/api/admin/create-admin/"
    headers = {'Authorization': f'Token {token}'}
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%H%M%S")
    
    data = {
        'username': f'testadmin_{timestamp}',
        'email': f'testadmin_{timestamp}@agriport.com',
        'first_name': 'Test',
        'last_name': 'Admin',
        'password': 'testadmin123',
        'is_superuser': False
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            if result.get('success'):
                admin_info = result.get('admin', {})
                print(f"✅ Admin created successfully!")
                print(f"Username: {admin_info.get('username')}")
                print(f"Email: {admin_info.get('email')}")
                print(f"ID: {admin_info.get('id')}")
            else:
                print(f"❌ Create admin failed: {result.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_manage_users(token):
    """Test manage users API"""
    if not token:
        print("❌ No token available for manage users test")
        return
        
    print("\n👥 Testing Manage Users API...")
    
    url = "http://localhost:8000/api/admin/manage-users/"
    headers = {'Authorization': f'Token {token}'}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                users = result.get('users', [])
                pagination = result.get('pagination', {})
                print(f"✅ Users retrieved successfully!")
                print(f"Users on page: {len(users)}")
                print(f"Total users: {pagination.get('total_users')}")
                print(f"Total pages: {pagination.get('total_pages')}")
                
                # Show first few users
                for i, user in enumerate(users[:3]):
                    print(f"  {i+1}. {user.get('username')} ({user.get('user_type')}) - {user.get('email')}")
            else:
                print(f"❌ Manage users failed: {result.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Run all admin API tests"""
    print("🚀 AGRIPORT ADMIN API TESTING")
    print("=" * 50)
    
    # Test admin login
    token = test_admin_login()
    
    if token:
        # Test other admin APIs
        test_admin_dashboard(token)
        test_create_admin(token)
        test_manage_users(token)
        
        print("\n✅ All admin API tests completed!")
    else:
        print("\n❌ Admin login failed - cannot test other APIs")

if __name__ == '__main__':
    main()
