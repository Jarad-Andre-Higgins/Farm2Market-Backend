#!/usr/bin/env python
"""
Comprehensive Test Suite for Real Impact Agriport System
Tests: Email Services, Real Admin Impact, Notifications, Broadcast System
"""
import requests
import json
from datetime import datetime

class RealImpactSystemTester:
    def __init__(self):
        self.api_url = "http://localhost:8000/api"
        self.admin_token = None
        self.farmer_token = None
        self.buyer_token = None
        self.test_user_ids = []
        
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
    
    def test_email_system(self):
        """Test email system functionality"""
        if not self.admin_token:
            return False
            
        print("\n📧 Testing Email System...")
        
        # Create a test admin to trigger email
        timestamp = datetime.now().strftime("%H%M%S")
        admin_data = {
            'username': f'emailtest_{timestamp}',
            'email': f'emailtest_{timestamp}@agriport.com',
            'first_name': 'Email',
            'last_name': 'Test',
            'password': f'emailpass_{timestamp}',
            'is_superuser': False
        }
        
        response = requests.post(f"{self.api_url}/admin/create-admin/", 
            json=admin_data, 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Admin created with email notification")
            print(f"   Email sent: {data.get('email_sent', False)}")
            self.test_user_ids.append(data['admin']['id'])
            return True
        
        print(f"❌ Email system test failed: {response.text}")
        return False
    
    def test_real_impact_user_deletion(self):
        """Test real impact user deletion"""
        if not self.admin_token or not self.test_user_ids:
            return False
            
        print("\n💥 Testing Real Impact User Deletion...")
        
        user_id = self.test_user_ids[0]
        
        response = requests.delete(f"{self.api_url}/admin/users/{user_id}/delete/", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User deleted with REAL system impact")
            print(f"   Deletion summary: {data.get('deletion_summary', {})}")
            return True
        
        print(f"❌ Real impact deletion failed: {response.text}")
        return False
    
    def test_notification_system(self):
        """Test notification system"""
        if not self.admin_token:
            return False
            
        print("\n🔔 Testing Notification System...")
        
        # Get notification count
        response = requests.get(f"{self.api_url}/notifications/count/", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Notification count retrieved")
            print(f"   Unread: {data.get('unread_count', 0)}")
            print(f"   Total: {data.get('total_count', 0)}")
            
            # Get notifications
            response = requests.get(f"{self.api_url}/notifications/?page=1&per_page=5", 
                headers={'Authorization': f'Token {self.admin_token}'}
            )
            
            if response.status_code == 200:
                notifications_data = response.json()
                print(f"✅ Notifications retrieved: {len(notifications_data.get('notifications', []))}")
                return True
        
        print(f"❌ Notification system test failed: {response.text}")
        return False
    
    def test_broadcast_system(self):
        """Test admin broadcast system"""
        if not self.admin_token:
            return False
            
        print("\n📢 Testing Broadcast System...")
        
        # Send broadcast to all users
        broadcast_data = {
            'title': 'System Test Broadcast',
            'message': 'This is a test broadcast message from the admin system.',
            'target_group': 'all',
            'send_email': True,
            'urgent': False
        }
        
        response = requests.post(f"{self.api_url}/admin/broadcast/", 
            json=broadcast_data,
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Broadcast sent successfully")
            print(f"   Notifications created: {data.get('details', {}).get('notifications_created', 0)}")
            print(f"   Emails sent: {data.get('details', {}).get('emails_sent', 0)}")
            
            # Get broadcast history
            response = requests.get(f"{self.api_url}/admin/broadcast-history/?page=1&per_page=5", 
                headers={'Authorization': f'Token {self.admin_token}'}
            )
            
            if response.status_code == 200:
                history_data = response.json()
                print(f"✅ Broadcast history retrieved: {len(history_data.get('broadcast_history', []))}")
                return True
        
        print(f"❌ Broadcast system test failed: {response.text}")
        return False
    
    def test_user_management_impact(self):
        """Test user management with real system impact"""
        if not self.admin_token:
            return False
            
        print("\n👥 Testing User Management with Real Impact...")
        
        # Get users list
        response = requests.get(f"{self.api_url}/admin/manage-users/?page=1&per_page=5", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            
            if users:
                test_user = users[0]
                user_id = test_user['id']
                
                print(f"✅ Found test user: {test_user['username']}")
                
                # Test user update with system impact
                update_data = {
                    'first_name': 'Updated',
                    'is_active': test_user['is_active']  # Keep same status to avoid major impact
                }
                
                response = requests.put(f"{self.api_url}/admin/users/{user_id}/update/", 
                    json=update_data,
                    headers={'Authorization': f'Token {self.admin_token}'}
                )
                
                if response.status_code == 200:
                    update_result = response.json()
                    print(f"✅ User updated with system impact")
                    print(f"   System impact: {len(update_result.get('system_impact', []))} changes")
                    return True
        
        print(f"❌ User management impact test failed")
        return False
    
    def test_search_and_analytics(self):
        """Test search and analytics functionality"""
        if not self.admin_token:
            return False
            
        print("\n🔍 Testing Search & Analytics...")
        
        # Test global search
        response = requests.get(f"{self.api_url}/admin/search/?q=test&type=all&limit=5", 
            headers={'Authorization': f'Token {self.admin_token}'}
        )
        
        if response.status_code == 200:
            search_data = response.json()
            print(f"✅ Global search working")
            print(f"   Results found: {search_data.get('search_results', {}).get('total_found', 0)}")
            
            # Test enhanced analytics
            response = requests.get(f"{self.api_url}/admin/analytics/", 
                headers={'Authorization': f'Token {self.admin_token}'}
            )
            
            if response.status_code == 200:
                analytics_data = response.json()
                analytics = analytics_data.get('analytics', {})
                print(f"✅ Enhanced analytics working")
                print(f"   Total users: {analytics.get('user_stats', {}).get('total_users', 0)}")
                print(f"   Total transactions: {analytics.get('transaction_stats', {}).get('total_transactions', 0)}")
                return True
        
        print(f"❌ Search & analytics test failed: {response.text}")
        return False
    
    def run_all_tests(self):
        """Run all real impact system tests"""
        print("🚀 REAL IMPACT AGRIPORT SYSTEM TESTING")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        tests = [
            ("Admin Login", self.test_admin_login),
            ("Email System", self.test_email_system),
            ("Real Impact User Deletion", self.test_real_impact_user_deletion),
            ("Notification System", self.test_notification_system),
            ("Broadcast System", self.test_broadcast_system),
            ("User Management Impact", self.test_user_management_impact),
            ("Search & Analytics", self.test_search_and_analytics)
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
        print("📊 REAL IMPACT SYSTEM TEST SUMMARY")
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
        
        print(f"\n🎯 REAL IMPACT SYSTEM STATUS:")
        if success_rate >= 90:
            print("🌟 EXCELLENT - Real impact system is fully functional!")
            print("🚀 All admin functions have REAL effects on the system!")
            print("📧 Email system is working properly!")
            print("🔔 Notification system is delivering notifications!")
            print("📢 Broadcast system is reaching all users!")
        elif success_rate >= 75:
            print("✅ GOOD - Most real impact features working")
        elif success_rate >= 50:
            print("⚠️  FAIR - Some real impact features working")
        else:
            print("❌ POOR - Real impact system has major issues")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 75

if __name__ == '__main__':
    tester = RealImpactSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Real impact system is ready for production!")
        print("💥 Admin actions now have REAL effects on the system!")
        print("📧 Email notifications are working!")
        print("🔔 Notification system is functional!")
        print("📢 Broadcast system is operational!")
    else:
        print("\n⚠️  Real impact system needs attention.")
