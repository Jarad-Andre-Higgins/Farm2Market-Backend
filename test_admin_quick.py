#!/usr/bin/env python
"""
Quick Test for Admin System Core Functions
"""
import requests
import json
from datetime import datetime

class QuickAdminTester:
    def __init__(self):
        self.api_url = "http://localhost:8000/api"
        self.admin_token = None
        
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
    
    def test_admin_dashboard(self):
        """Test admin dashboard"""
        if not self.admin_token:
            return False
            
        print("\n📊 Testing Admin Dashboard...")
        
        response = requests.get(f"{self.api_url}/admin/dashboard/", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dashboard loaded successfully")
            print(f"   Total users: {data.get('total_users', 0)}")
            print(f"   Pending farmers: {data.get('pending_farmers', 0)}")
            return True
        
        print(f"❌ Dashboard failed: {response.text}")
        return False
    
    def test_user_management(self):
        """Test user management"""
        if not self.admin_token:
            return False
            
        print("\n👥 Testing User Management...")
        
        response = requests.get(f"{self.api_url}/admin/manage-users/", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User management working")
            print(f"   Users found: {len(data.get('users', []))}")
            return True
        
        print(f"❌ User management failed: {response.text}")
        return False
    
    def test_admin_creation(self):
        """Test admin creation"""
        if not self.admin_token:
            return False
            
        print("\n👤 Testing Admin Creation...")
        
        timestamp = datetime.now().strftime("%H%M%S")
        admin_data = {
            'username': f'quicktest_{timestamp}',
            'email': f'quicktest_{timestamp}@agriport.com',
            'first_name': 'Quick',
            'last_name': 'Test',
            'password': f'quickpass_{timestamp}',
            'is_superuser': False
        }
        
        response = requests.post(f"{self.api_url}/admin/create-admin/", 
            json=admin_data, 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Admin created successfully")
            print(f"   Username: {data['admin']['username']}")
            print(f"   Email sent: {data.get('email_sent', False)}")
            return True
        
        print(f"❌ Admin creation failed: {response.text}")
        return False
    
    def test_roles_system(self):
        """Test roles system"""
        if not self.admin_token:
            return False
            
        print("\n🔐 Testing Roles System...")
        
        response = requests.get(f"{self.api_url}/admin/roles/", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Roles system working")
            print(f"   Available roles: {len(data.get('roles', []))}")
            return True
        
        print(f"❌ Roles system failed: {response.text}")
        return False
    
    def run_quick_tests(self):
        """Run quick admin system tests"""
        print("🚀 QUICK ADMIN SYSTEM TEST")
        print("=" * 50)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        tests = [
            ("Admin Login", self.test_admin_login),
            ("Admin Dashboard", self.test_admin_dashboard),
            ("User Management", self.test_user_management),
            ("Admin Creation", self.test_admin_creation),
            ("Roles System", self.test_roles_system)
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
        print("\n" + "=" * 50)
        print("📊 QUICK TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 RESULTS:")
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")
        
        if success_rate >= 80:
            print(f"\n🎉 EXCELLENT - Core admin system working!")
        elif success_rate >= 60:
            print(f"\n✅ GOOD - Most core functions working")
        else:
            print(f"\n⚠️  NEEDS ATTENTION - Core issues found")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 60

if __name__ == '__main__':
    tester = QuickAdminTester()
    success = tester.run_quick_tests()
    
    if success:
        print("\n🎉 Core admin system is working!")
    else:
        print("\n⚠️  Core admin system needs fixes.")
