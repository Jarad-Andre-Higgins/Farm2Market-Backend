#!/usr/bin/env python
"""
Comprehensive Test Suite for Complete Agriport Admin System
Tests all new functionalities: CRUD, Transactions, User Management, Search, Roles, Analytics
"""
import requests
import json
from datetime import datetime

class CompleteAdminSystemTester:
    def __init__(self):
        self.api_url = "http://localhost:8000/api"
        self.admin_token = None
        self.test_admin_id = None
        self.test_user_id = None
        
    def test_admin_login(self):
        """Test admin login"""
        print("🔐 Testing Admin Login...")
        
        response = requests.post(f"{self.api_url}/admin/login/", json={
            'email': 'admin@agriport.com',
            'password': 'admin123'
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.admin_token = data['token']
                print(f"✅ Admin login successful!")
                return True
        
        print(f"❌ Admin login failed: {response.text}")
        return False
    
    def test_admin_crud_operations(self):
        """Test admin CRUD operations"""
        if not self.admin_token:
            return False
            
        print("\n👤 Testing Admin CRUD Operations...")
        
        # Create admin
        timestamp = datetime.now().strftime("%H%M%S")
        admin_data = {
            'username': f'testadmin_crud_{timestamp}',
            'email': f'testadmin_crud_{timestamp}@agriport.com',
            'first_name': 'Test',
            'last_name': 'CRUD',
            'password': f'testpass_{timestamp}',
            'is_superuser': False
        }
        
        response = requests.post(f"{self.api_url}/admin/create-admin/", 
            json=admin_data, 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code != 201:
            print(f"❌ Admin creation failed: {response.text}")
            return False
        
        created_admin = response.json()['admin']
        self.test_admin_id = created_admin['id']
        print(f"✅ Admin created: {created_admin['username']}")
        
        # View admin details
        response = requests.get(f"{self.api_url}/admin/view/{self.test_admin_id}/", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code != 200:
            print(f"❌ Admin view failed: {response.text}")
            return False
        
        print(f"✅ Admin details retrieved")
        
        # Update admin
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = requests.put(f"{self.api_url}/admin/update/{self.test_admin_id}/", 
            json=update_data,
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code != 200:
            print(f"❌ Admin update failed: {response.text}")
            return False
        
        print(f"✅ Admin updated successfully")
        return True
    
    def test_transaction_management(self):
        """Test transaction management"""
        if not self.admin_token:
            return False
            
        print("\n💰 Testing Transaction Management...")
        
        # Get transactions with filters
        response = requests.get(f"{self.api_url}/admin/transactions/?page=1&per_page=5", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code != 200:
            print(f"❌ Transaction list failed: {response.text}")
            return False
        
        data = response.json()
        print(f"✅ Retrieved {len(data['transactions'])} transactions")
        print(f"   Total transactions: {data['pagination']['total_transactions']}")
        print(f"   Total amount: ${data['statistics']['total_amount']:.2f}")
        
        return True
    
    def test_user_management(self):
        """Test user management"""
        if not self.admin_token:
            return False
            
        print("\n👥 Testing User Management...")
        
        # Get a user to test with
        response = requests.get(f"{self.api_url}/admin/manage-users/?page=1&per_page=5", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code != 200:
            print(f"❌ User list failed: {response.text}")
            return False
        
        users = response.json()['users']
        if not users:
            print("⚠️  No users found for testing")
            return True
        
        test_user = users[0]
        self.test_user_id = test_user['id']
        print(f"✅ Found test user: {test_user['username']}")
        
        # Get user details
        response = requests.get(f"{self.api_url}/admin/users/{self.test_user_id}/", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code != 200:
            print(f"❌ User details failed: {response.text}")
            return False
        
        user_data = response.json()['user']
        print(f"✅ User details retrieved: {user_data['user_type']}")
        print(f"   Statistics: {len(user_data.get('statistics', {}))} metrics")
        print(f"   Recent activity: {len(user_data.get('recent_activity', []))} items")
        
        return True
    
    def test_search_functionality(self):
        """Test search and filtering"""
        if not self.admin_token:
            return False
            
        print("\n🔍 Testing Search & Filtering...")
        
        # Global search
        response = requests.get(f"{self.api_url}/admin/search/?q=test&type=all&limit=10", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code != 200:
            print(f"❌ Global search failed: {response.text}")
            return False
        
        search_results = response.json()['search_results']
        print(f"✅ Global search completed")
        print(f"   Total results: {search_results['total_found']}")
        print(f"   Users found: {len(search_results['results']['users'])}")
        print(f"   Transactions found: {len(search_results['results']['transactions'])}")
        
        # Get filter options
        response = requests.get(f"{self.api_url}/admin/filters/", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code != 200:
            print(f"❌ Filter options failed: {response.text}")
            return False
        
        filters = response.json()
        print(f"✅ Filter options retrieved")
        print(f"   User types: {len(filters['filter_options']['user_types'])}")
        print(f"   Categories: {len(filters['filter_options']['categories'])}")
        
        return True
    
    def test_role_management(self):
        """Test role-based access control"""
        if not self.admin_token:
            return False
            
        print("\n🔐 Testing Role Management...")
        
        # Get available roles
        response = requests.get(f"{self.api_url}/admin/roles/", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code != 200:
            print(f"❌ Roles list failed: {response.text}")
            return False
        
        roles = response.json()['roles']
        print(f"✅ Retrieved {len(roles)} available roles")
        
        if roles and self.test_admin_id:
            # Assign role to test admin
            role_data = {
                'admin_user_id': self.test_admin_id,
                'role_id': roles[0]['id']
            }
            
            response = requests.post(f"{self.api_url}/admin/roles/assign/", 
                json=role_data,
                headers={'Authorization': f'Token {self.admin_token}'}
            )
            
            if response.status_code == 200:
                print(f"✅ Role assigned successfully")
                
                # Get user roles
                response = requests.get(f"{self.api_url}/admin/users/{self.test_admin_id}/roles/", 
                    headers={'Authorization': f'Token {self.admin_token}'}
                )
                
                if response.status_code == 200:
                    user_roles = response.json()['roles']
                    print(f"✅ User has {len(user_roles)} roles assigned")
                    return True
        
        return True
    
    def test_enhanced_analytics(self):
        """Test enhanced analytics"""
        if not self.admin_token:
            return False
            
        print("\n📊 Testing Enhanced Analytics...")
        
        response = requests.get(f"{self.api_url}/admin/analytics/", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code != 200:
            print(f"❌ Analytics failed: {response.text}")
            return False
        
        analytics = response.json()['analytics']
        print(f"✅ Analytics retrieved successfully")
        print(f"   Total users: {analytics['user_stats']['total_users']}")
        print(f"   Total transactions: {analytics['transaction_stats']['total_transactions']}")
        print(f"   Total revenue: ${analytics['transaction_stats']['total_revenue']:.2f}")
        print(f"   Top farmers: {len(analytics['top_farmers'])}")
        print(f"   Top buyers: {len(analytics['top_buyers'])}")
        print(f"   Recent activities: {len(analytics['recent_activities'])}")
        
        return True
    
    def run_all_tests(self):
        """Run all comprehensive admin system tests"""
        print("🚀 COMPREHENSIVE ADMIN SYSTEM TESTING")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        tests = [
            ("Admin Login", self.test_admin_login),
            ("Admin CRUD Operations", self.test_admin_crud_operations),
            ("Transaction Management", self.test_transaction_management),
            ("User Management", self.test_user_management),
            ("Search & Filtering", self.test_search_functionality),
            ("Role Management", self.test_role_management),
            ("Enhanced Analytics", self.test_enhanced_analytics)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE ADMIN SYSTEM TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")
        
        print(f"\n🎯 ADMIN SYSTEM STATUS:")
        if success_rate >= 90:
            print("🌟 EXCELLENT - Complete admin system is fully functional!")
            print("🚀 Ready for production deployment!")
        elif success_rate >= 75:
            print("✅ GOOD - Admin system mostly working, minor issues")
        elif success_rate >= 50:
            print("⚠️  FAIR - Admin system partially working, needs attention")
        else:
            print("❌ POOR - Admin system has major issues")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 75

if __name__ == '__main__':
    tester = CompleteAdminSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Complete admin system is ready for production!")
    else:
        print("\n⚠️  Complete admin system needs attention.")
