#!/usr/bin/env python
"""
Test Enhanced Admin System with Email Notifications and Password Duplication Prevention
"""
import requests
import json
from datetime import datetime

class EnhancedAdminTester:
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
    
    def test_password_duplication_prevention(self):
        """Test password duplication prevention"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        print("\n🔒 Testing Password Duplication Prevention...")
        
        # Try to create admin with existing password
        admin_data = {
            'username': f'testadmin_dup_{datetime.now().strftime("%H%M%S")}',
            'email': f'testadmin_dup_{datetime.now().strftime("%H%M%S")}@agriport.com',
            'first_name': 'Test',
            'last_name': 'Duplicate',
            'password': 'admin123',  # Same as superadmin password
            'is_superuser': False
        }
        
        response = requests.post(f"{self.api_url}/admin/create-admin/", 
            json=admin_data, 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 400:
            data = response.json()
            if 'password is already in use' in data.get('error', '').lower():
                print(f"✅ Password duplication prevented successfully!")
                print(f"   Error message: {data.get('error')}")
                return True
        
        print(f"❌ Password duplication not prevented: {response.text}")
        return False
    
    def test_admin_creation_with_email(self):
        """Test admin creation with email notification"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        print("\n📧 Testing Admin Creation with Email Notification...")
        
        timestamp = datetime.now().strftime("%H%M%S")
        admin_data = {
            'username': f'testadmin_email_{timestamp}',
            'email': f'testadmin_email_{timestamp}@agriport.com',
            'first_name': 'Test',
            'last_name': 'Email',
            'password': f'uniquepass_{timestamp}',
            'is_superuser': False
        }
        
        response = requests.post(f"{self.api_url}/admin/create-admin/", 
            json=admin_data, 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 201:
            data = response.json()
            if data.get('success'):
                print(f"✅ Admin created successfully!")
                print(f"   Username: {data.get('admin', {}).get('username')}")
                print(f"   Email: {data.get('admin', {}).get('email')}")
                print(f"   Email sent: {data.get('email_sent', 'Unknown')}")
                print(f"   Message: {data.get('message')}")
                return True
        
        print(f"❌ Admin creation failed: {response.text}")
        return False
    
    def test_duplicate_email_prevention(self):
        """Test duplicate email prevention"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        print("\n📧 Testing Duplicate Email Prevention...")
        
        # Try to create admin with existing email
        admin_data = {
            'username': 'different_username',
            'email': 'admin@agriport.com',  # Existing email
            'first_name': 'Test',
            'last_name': 'Duplicate',
            'password': 'uniquepassword123',
            'is_superuser': False
        }
        
        response = requests.post(f"{self.api_url}/admin/create-admin/", 
            json=admin_data, 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 400:
            data = response.json()
            if 'email already exists' in data.get('error', '').lower():
                print(f"✅ Duplicate email prevented successfully!")
                print(f"   Error message: {data.get('error')}")
                return True
        
        print(f"❌ Duplicate email not prevented: {response.text}")
        return False
    
    def test_duplicate_username_prevention(self):
        """Test duplicate username prevention"""
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        print("\n👤 Testing Duplicate Username Prevention...")
        
        # Try to create admin with existing username
        admin_data = {
            'username': 'superadmin',  # Existing username
            'email': 'different@email.com',
            'first_name': 'Test',
            'last_name': 'Duplicate',
            'password': 'uniquepassword456',
            'is_superuser': False
        }
        
        response = requests.post(f"{self.api_url}/admin/create-admin/", 
            json=admin_data, 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 400:
            data = response.json()
            if 'username already exists' in data.get('error', '').lower():
                print(f"✅ Duplicate username prevented successfully!")
                print(f"   Error message: {data.get('error')}")
                return True
        
        print(f"❌ Duplicate username not prevented: {response.text}")
        return False
    
    def test_farmer_registration_password_duplication(self):
        """Test password duplication prevention in farmer registration"""
        print("\n🚜 Testing Farmer Registration Password Duplication...")
        
        farmer_data = {
            'username': f'testfarmer_dup_{datetime.now().strftime("%H%M%S")}',
            'email': f'testfarmer_dup_{datetime.now().strftime("%H%M%S")}@farm.com',
            'password': 'admin123',  # Same as admin password
            'password_confirm': 'admin123',
            'first_name': 'Test',
            'last_name': 'Farmer',
            'user_type': 'Farmer',
            'phone_number': '1234567890'
        }
        
        response = requests.post(f"{self.api_url}/farmer/register/", json=farmer_data)
        
        if response.status_code == 400:
            data = response.json()
            if 'password is already in use' in str(data).lower():
                print(f"✅ Farmer password duplication prevented!")
                return True
        
        print(f"❌ Farmer password duplication not prevented: {response.text}")
        return False
    
    def run_all_tests(self):
        """Run all enhanced admin tests"""
        print("🚀 TESTING ENHANCED ADMIN SYSTEM")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        tests = [
            ("Admin Login", self.test_admin_login),
            ("Password Duplication Prevention", self.test_password_duplication_prevention),
            ("Admin Creation with Email", self.test_admin_creation_with_email),
            ("Duplicate Email Prevention", self.test_duplicate_email_prevention),
            ("Duplicate Username Prevention", self.test_duplicate_username_prevention),
            ("Farmer Password Duplication", self.test_farmer_registration_password_duplication)
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
        print("\n" + "=" * 60)
        print("📊 ENHANCED ADMIN SYSTEM TEST SUMMARY")
        print("=" * 60)
        
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
        
        if success_rate >= 80:
            print(f"\n🎉 EXCELLENT! Enhanced admin system is working perfectly!")
        elif success_rate >= 60:
            print(f"\n⚠️  GOOD! Most features working, some issues to address.")
        else:
            print(f"\n❌ NEEDS ATTENTION! Multiple issues found.")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 80

if __name__ == '__main__':
    tester = EnhancedAdminTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Enhanced admin system is ready for production!")
    else:
        print("\n⚠️  Enhanced admin system needs attention.")
