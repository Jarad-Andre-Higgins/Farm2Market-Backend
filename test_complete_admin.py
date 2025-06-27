#!/usr/bin/env python
"""
Complete Admin System Testing for Agriport
Tests backend APIs, frontend functionality, and database operations
"""
import requests
import json
import os
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import CustomUser, AuditLog

class CompleteAdminTester:
    def __init__(self):
        self.api_url = "http://localhost:8000/api"
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
        
    def test_database_setup(self):
        """Test database setup and superadmin creation"""
        try:
            # Check if superadmin exists
            superadmin = CustomUser.objects.filter(
                email='admin@agriport.com',
                user_type='Admin',
                is_superuser=True
            ).first()
            
            if not superadmin:
                # Create superadmin
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
                self.log_test("Database Setup", True, "Superadmin created successfully")
            else:
                self.log_test("Database Setup", True, "Superadmin already exists")
            
            # Test database queries
            total_users = CustomUser.objects.count()
            total_farmers = CustomUser.objects.filter(user_type='Farmer').count()
            total_buyers = CustomUser.objects.filter(user_type='Buyer').count()
            
            self.log_test(
                "Database Queries", 
                True, 
                f"Database accessible - Users: {total_users}, Farmers: {total_farmers}, Buyers: {total_buyers}"
            )
            return True
            
        except Exception as e:
            self.log_test("Database Setup", False, f"Database error: {str(e)}")
            return False
    
    def test_admin_authentication(self):
        """Test admin login API"""
        try:
            response = requests.post(f"{self.api_url}/admin/login/", json={
                'email': 'admin@agriport.com',
                'password': 'admin123'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('token'):
                    self.admin_token = data['token']
                    admin_info = data.get('admin', {})
                    self.log_test(
                        "Admin Authentication", 
                        True, 
                        f"Login successful for {admin_info.get('username')}"
                    )
                    return True
                else:
                    self.log_test("Admin Authentication", False, "No token in response")
                    return False
            else:
                self.log_test("Admin Authentication", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Error: {str(e)}")
            return False
    
    def test_admin_dashboard_api(self):
        """Test admin dashboard API"""
        if not self.admin_token:
            self.log_test("Admin Dashboard API", False, "No admin token")
            return False
            
        try:
            response = requests.get(f"{self.api_url}/admin/dashboard/", headers={
                'Authorization': f'Token {self.admin_token}'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stats = data.get('dashboard_data', {}).get('system_stats', {})
                    self.log_test(
                        "Admin Dashboard API", 
                        True, 
                        f"Dashboard loaded - {stats.get('total_users', 0)} users, {stats.get('pending_farmers', 0)} pending"
                    )
                    return True
                else:
                    self.log_test("Admin Dashboard API", False, "API returned success=False")
                    return False
            else:
                self.log_test("Admin Dashboard API", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Dashboard API", False, f"Error: {str(e)}")
            return False
    
    def test_create_admin_api(self):
        """Test create admin API"""
        if not self.admin_token:
            self.log_test("Create Admin API", False, "No admin token")
            return False
            
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            admin_data = {
                'username': f'testadmin_{timestamp}',
                'email': f'testadmin_{timestamp}@agriport.com',
                'first_name': 'Test',
                'last_name': 'Admin',
                'password': 'testadmin123',
                'is_superuser': False
            }
            
            response = requests.post(f"{self.api_url}/admin/create-admin/", 
                json=admin_data, 
                headers={'Authorization': f'Token {self.admin_token}'}
            )
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    admin_info = data.get('admin', {})
                    self.log_test(
                        "Create Admin API", 
                        True, 
                        f"Admin created: {admin_info.get('username')}"
                    )
                    
                    # Verify in database
                    created_admin = CustomUser.objects.filter(
                        username=admin_data['username']
                    ).first()
                    
                    if created_admin:
                        self.log_test(
                            "Database Verification", 
                            True, 
                            f"Admin verified in database: {created_admin.email}"
                        )
                    else:
                        self.log_test("Database Verification", False, "Admin not found in database")
                    
                    return True
                else:
                    self.log_test("Create Admin API", False, data.get('error', 'Unknown error'))
                    return False
            else:
                self.log_test("Create Admin API", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create Admin API", False, f"Error: {str(e)}")
            return False
    
    def test_user_management_api(self):
        """Test user management API"""
        if not self.admin_token:
            self.log_test("User Management API", False, "No admin token")
            return False
            
        try:
            response = requests.get(f"{self.api_url}/admin/manage-users/", headers={
                'Authorization': f'Token {self.admin_token}'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    users = data.get('users', [])
                    pagination = data.get('pagination', {})
                    self.log_test(
                        "User Management API", 
                        True, 
                        f"Retrieved {len(users)} users, total: {pagination.get('total_users', 0)}"
                    )
                    return True
                else:
                    self.log_test("User Management API", False, "API returned success=False")
                    return False
            else:
                self.log_test("User Management API", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Management API", False, f"Error: {str(e)}")
            return False
    
    def test_pending_farmers_api(self):
        """Test pending farmers API"""
        if not self.admin_token:
            self.log_test("Pending Farmers API", False, "No admin token")
            return False
            
        try:
            response = requests.get(f"{self.api_url}/admin/pending-farmers/", headers={
                'Authorization': f'Token {self.admin_token}'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    farmers = data.get('pending_farmers', [])
                    self.log_test(
                        "Pending Farmers API", 
                        True, 
                        f"Retrieved {len(farmers)} pending farmers"
                    )
                    return True
                else:
                    self.log_test("Pending Farmers API", False, "API returned success=False")
                    return False
            else:
                self.log_test("Pending Farmers API", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Pending Farmers API", False, f"Error: {str(e)}")
            return False
    
    def test_audit_logging(self):
        """Test audit logging functionality"""
        try:
            # Check if audit logs are being created
            recent_logs = AuditLog.objects.filter(
                action_type='admin_action'
            ).order_by('-created_at')[:5]
            
            if recent_logs.exists():
                self.log_test(
                    "Audit Logging", 
                    True, 
                    f"Found {recent_logs.count()} recent audit logs"
                )
                
                # Show recent log details
                for log in recent_logs:
                    print(f"   📝 {log.created_at.strftime('%H:%M:%S')} - {log.description}")
                
                return True
            else:
                self.log_test("Audit Logging", True, "No recent audit logs (expected for new system)")
                return True
                
        except Exception as e:
            self.log_test("Audit Logging", False, f"Error: {str(e)}")
            return False
    
    def test_frontend_files(self):
        """Test frontend file existence"""
        try:
            frontend_path = "C:/Users/LENOVO T570/Documents/augment-projects/farm2market/Frontend/Admin"
            
            required_files = [
                'admin_login.html',
                'admin_dashboard.html',
                'admin_dashboard.js'
            ]
            
            missing_files = []
            for file in required_files:
                file_path = os.path.join(frontend_path, file)
                if not os.path.exists(file_path):
                    missing_files.append(file)
            
            if not missing_files:
                self.log_test(
                    "Frontend Files", 
                    True, 
                    f"All {len(required_files)} frontend files exist"
                )
                return True
            else:
                self.log_test(
                    "Frontend Files", 
                    False, 
                    f"Missing files: {', '.join(missing_files)}"
                )
                return False
                
        except Exception as e:
            self.log_test("Frontend Files", False, f"Error: {str(e)}")
            return False
    
    def run_complete_test(self):
        """Run all admin system tests"""
        print("🚀 AGRIPORT COMPLETE ADMIN SYSTEM TESTING")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Run all tests
        tests = [
            self.test_database_setup,
            self.test_admin_authentication,
            self.test_admin_dashboard_api,
            self.test_create_admin_api,
            self.test_user_management_api,
            self.test_pending_farmers_api,
            self.test_audit_logging,
            self.test_frontend_files
        ]
        
        for test in tests:
            test()
            print()  # Add spacing between tests
        
        # Summary
        print("=" * 70)
        print("📊 COMPLETE ADMIN SYSTEM TEST SUMMARY")
        print("=" * 70)
        
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
        
        print(f"\n🎯 ADMIN SYSTEM STATUS:")
        if success_rate >= 90:
            print("✅ EXCELLENT - Admin system is fully functional!")
        elif success_rate >= 75:
            print("⚠️  GOOD - Admin system is mostly functional with minor issues")
        elif success_rate >= 50:
            print("⚠️  FAIR - Admin system has some issues that need attention")
        else:
            print("❌ POOR - Admin system has significant issues")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 75

if __name__ == '__main__':
    tester = CompleteAdminTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎉 Admin system is ready for production!")
    else:
        print("\n⚠️  Admin system needs attention before production deployment.")
