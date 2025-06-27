#!/usr/bin/env python
"""
Comprehensive Admin System Testing Script for Agriport
Tests all admin functionalities including API endpoints
"""
import requests
import json
import sys
from datetime import datetime

class AgriportAdminTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", data=None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'data': data,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {test_name}: {message}")
        if data and success:
            print(f"   📊 Data: {json.dumps(data, indent=2)[:200]}...")
        
    def create_superadmin(self):
        """Create initial superadmin if not exists"""
        try:
            print("\n🔧 CREATING INITIAL SUPERADMIN...")
            
            # Try to create superadmin via Django management
            import os
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
            
            import django
            django.setup()
            
            from farm2market_backend.coreF2M.models import CustomUser
            
            # Check if superadmin exists
            if not CustomUser.objects.filter(is_superuser=True, user_type='Admin').exists():
                superadmin = CustomUser.objects.create_user(
                    username='superadmin',
                    email='admin@agriport.com',
                    password='admin123',
                    first_name='Super',
                    last_name='Admin',
                    user_type='Admin',
                    is_approved=True,
                    is_active=True,
                    is_staff=True,
                    is_superuser=True
                )
                print(f"✅ Superadmin created: {superadmin.email}")
                return True
            else:
                print("✅ Superadmin already exists")
                return True
                
        except Exception as e:
            print(f"❌ Error creating superadmin: {e}")
            return False
    
    def test_admin_login(self):
        """Test admin login functionality"""
        try:
            print("\n🔐 TESTING ADMIN LOGIN...")
            
            # Test with superadmin credentials
            login_data = {
                'email': 'admin@agriport.com',
                'password': 'admin123'
            }
            
            response = requests.post(f"{self.api_url}/admin/login/", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('token'):
                    self.admin_token = data['token']
                    admin_info = data.get('admin', {})
                    self.log_test(
                        "Admin Login", 
                        True, 
                        f"Login successful for {admin_info.get('email')}", 
                        {
                            'admin_id': admin_info.get('id'),
                            'username': admin_info.get('username'),
                            'is_superuser': admin_info.get('is_superuser')
                        }
                    )
                    return True
                else:
                    self.log_test("Admin Login", False, "No token in response")
                    return False
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Error: {str(e)}")
            return False
    
    def test_admin_dashboard(self):
        """Test admin dashboard data"""
        if not self.admin_token:
            self.log_test("Admin Dashboard", False, "No admin token available")
            return False
            
        try:
            headers = {'Authorization': f'Token {self.admin_token}'}
            response = requests.get(f"{self.api_url}/admin/dashboard/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    dashboard_data = data.get('dashboard_data', {})
                    system_stats = dashboard_data.get('system_stats', {})
                    
                    self.log_test(
                        "Admin Dashboard", 
                        True, 
                        "Dashboard data retrieved successfully",
                        {
                            'total_users': system_stats.get('total_users'),
                            'total_farmers': system_stats.get('total_farmers'),
                            'total_buyers': system_stats.get('total_buyers'),
                            'pending_farmers': system_stats.get('pending_farmers'),
                            'active_listings': system_stats.get('active_listings')
                        }
                    )
                    return True
                else:
                    self.log_test("Admin Dashboard", False, "API returned success=False")
                    return False
            else:
                self.log_test("Admin Dashboard", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Dashboard", False, f"Error: {str(e)}")
            return False
    
    def test_create_admin(self):
        """Test creating a new admin"""
        if not self.admin_token:
            self.log_test("Create Admin", False, "No admin token available")
            return False
            
        try:
            headers = {'Authorization': f'Token {self.admin_token}'}
            
            # Create test admin data
            admin_data = {
                'username': f'testadmin_{datetime.now().strftime("%H%M%S")}',
                'email': f'testadmin_{datetime.now().strftime("%H%M%S")}@agriport.com',
                'first_name': 'Test',
                'last_name': 'Admin',
                'password': 'testadmin123',
                'is_superuser': False
            }
            
            response = requests.post(f"{self.api_url}/admin/create-admin/", json=admin_data, headers=headers)
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    admin_info = data.get('admin', {})
                    self.log_test(
                        "Create Admin", 
                        True, 
                        f"Admin created successfully: {admin_info.get('username')}",
                        {
                            'admin_id': admin_info.get('id'),
                            'username': admin_info.get('username'),
                            'email': admin_info.get('email'),
                            'is_superuser': admin_info.get('is_superuser')
                        }
                    )
                    return True
                else:
                    self.log_test("Create Admin", False, "API returned success=False")
                    return False
            else:
                self.log_test("Create Admin", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Admin", False, f"Error: {str(e)}")
            return False
    
    def test_manage_users(self):
        """Test user management functionality"""
        if not self.admin_token:
            self.log_test("Manage Users", False, "No admin token available")
            return False
            
        try:
            headers = {'Authorization': f'Token {self.admin_token}'}
            
            # Test getting all users
            response = requests.get(f"{self.api_url}/admin/manage-users/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    users = data.get('users', [])
                    pagination = data.get('pagination', {})
                    
                    self.log_test(
                        "Manage Users", 
                        True, 
                        f"Retrieved {len(users)} users",
                        {
                            'total_users': pagination.get('total_users'),
                            'current_page': pagination.get('current_page'),
                            'total_pages': pagination.get('total_pages')
                        }
                    )
                    return True
                else:
                    self.log_test("Manage Users", False, "API returned success=False")
                    return False
            else:
                self.log_test("Manage Users", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Manage Users", False, f"Error: {str(e)}")
            return False
    
    def test_pending_farmers(self):
        """Test pending farmers functionality"""
        if not self.admin_token:
            self.log_test("Pending Farmers", False, "No admin token available")
            return False
            
        try:
            headers = {'Authorization': f'Token {self.admin_token}'}
            response = requests.get(f"{self.api_url}/admin/pending-farmers/", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    pending_farmers = data.get('pending_farmers', [])
                    
                    self.log_test(
                        "Pending Farmers", 
                        True, 
                        f"Retrieved {len(pending_farmers)} pending farmers",
                        {'count': len(pending_farmers)}
                    )
                    return True
                else:
                    self.log_test("Pending Farmers", False, "API returned success=False")
                    return False
            else:
                self.log_test("Pending Farmers", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Pending Farmers", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all admin system tests"""
        print("🚀 STARTING AGRIPORT ADMIN SYSTEM TESTS")
        print("=" * 60)
        print(f"Testing API at: {self.api_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Step 1: Create superadmin
        if not self.create_superadmin():
            print("❌ Failed to create superadmin. Aborting tests.")
            return
        
        # Step 2: Test admin login
        if not self.test_admin_login():
            print("❌ Admin login failed. Aborting remaining tests.")
            return
        
        # Step 3: Test all admin functionalities
        self.test_admin_dashboard()
        self.test_create_admin()
        self.test_manage_users()
        self.test_pending_farmers()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 ADMIN SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test_name']}: {result['message']}")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    tester = AgriportAdminTester()
    tester.run_all_tests()
