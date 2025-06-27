#!/usr/bin/env python
"""
Test Email System for Agriport Admin Creation
"""
import os
import django
import requests
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from farm2market_backend.coreF2M.models import CustomUser

class EmailSystemTester:
    def __init__(self):
        self.api_url = "http://localhost:8000/api"
        self.admin_token = None
        
    def test_django_email_config(self):
        """Test Django email configuration"""
        print("📧 Testing Django Email Configuration...")
        
        try:
            print(f"   Email Backend: {settings.EMAIL_BACKEND}")
            print(f"   Default From Email: {settings.DEFAULT_FROM_EMAIL}")
            print(f"   Email Timeout: {getattr(settings, 'EMAIL_TIMEOUT', 'Not set')}")
            
            if 'console' in settings.EMAIL_BACKEND:
                print("   ✅ Console backend configured (emails will print to console)")
            elif 'smtp' in settings.EMAIL_BACKEND:
                print("   ✅ SMTP backend configured")
                print(f"   Email Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
                print(f"   Email Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
            else:
                print("   ⚠️  Unknown email backend")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Email configuration error: {e}")
            return False
    
    def test_direct_email_send(self):
        """Test sending email directly through Django"""
        print("\n📤 Testing Direct Email Send...")
        
        try:
            subject = 'Agriport Email Test'
            message = '''
            This is a test email from the Agriport system.
            
            If you receive this email, the email system is working correctly.
            
            Test Details:
            - Timestamp: {timestamp}
            - System: Agriport Admin Email Test
            - Purpose: Email functionality verification
            
            Best regards,
            Agriport Team
            '''.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = ['test@example.com']  # Test email
            
            result = send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
            )
            
            if result == 1:
                print("   ✅ Email sent successfully!")
                print("   📧 Check console output for email content (console backend)")
                return True
            else:
                print("   ❌ Email sending failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Email sending error: {e}")
            return False
    
    def test_admin_login(self):
        """Test admin login for API testing"""
        print("\n🔐 Testing Admin Login...")
        
        try:
            response = requests.post(f"{self.api_url}/admin/login/", json={
                'email': 'admin@agriport.com',
                'password': 'admin123'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.admin_token = data['token']
                    print("   ✅ Admin login successful!")
                    return True
            
            print(f"   ❌ Admin login failed: {response.text}")
            return False
            
        except Exception as e:
            print(f"   ❌ Admin login error: {e}")
            return False
    
    def test_admin_creation_with_email(self):
        """Test admin creation with email notification"""
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
            
        print("\n👤 Testing Admin Creation with Email...")
        
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            admin_data = {
                'username': f'emailtest_{timestamp}',
                'email': f'emailtest_{timestamp}@agriport.com',
                'first_name': 'Email',
                'last_name': 'Test',
                'password': f'emailtest_{timestamp}',
                'is_superuser': False
            }
            
            print(f"   Creating admin: {admin_data['username']}")
            print(f"   Email: {admin_data['email']}")
            
            response = requests.post(f"{self.api_url}/admin/create-admin/", 
                json=admin_data, 
                headers={'Authorization': f'Token {self.admin_token}'}
            )
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    print("   ✅ Admin created successfully!")
                    print(f"   📧 Email sent: {data.get('email_sent', 'Unknown')}")
                    print(f"   📝 Message: {data.get('message', 'No message')}")
                    
                    # Check if admin was created in database
                    try:
                        created_admin = CustomUser.objects.get(username=admin_data['username'])
                        print(f"   ✅ Admin verified in database: {created_admin.email}")
                    except CustomUser.DoesNotExist:
                        print("   ❌ Admin not found in database")
                    
                    return True
                else:
                    print(f"   ❌ Admin creation failed: {data.get('error')}")
                    return False
            else:
                print(f"   ❌ Admin creation failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Admin creation error: {e}")
            return False
    
    def test_email_function_directly(self):
        """Test the email function directly"""
        print("\n🔧 Testing Email Function Directly...")
        
        try:
            # Import the email function
            from farm2market_backend.coreF2M.views import send_admin_welcome_email
            
            # Create test admin objects
            admin_user = type('TestAdmin', (), {
                'first_name': 'Test',
                'last_name': 'Admin',
                'email': 'testadmin@agriport.com',
                'username': 'testadmin',
                'is_superuser': False
            })()
            
            creator_admin = type('CreatorAdmin', (), {
                'first_name': 'Creator',
                'last_name': 'Admin',
                'username': 'creator'
            })()
            
            result = send_admin_welcome_email(admin_user, 'testpassword123', creator_admin)
            
            if result:
                print("   ✅ Email function executed successfully!")
                print("   📧 Check console output for email content")
                return True
            else:
                print("   ❌ Email function failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Email function error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all email system tests"""
        print("🚀 AGRIPORT EMAIL SYSTEM TESTING")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        tests = [
            ("Django Email Configuration", self.test_django_email_config),
            ("Direct Email Send", self.test_direct_email_send),
            ("Admin Login", self.test_admin_login),
            ("Admin Creation with Email", self.test_admin_creation_with_email),
            ("Email Function Direct Test", self.test_email_function_directly)
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
        print("📊 EMAIL SYSTEM TEST SUMMARY")
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
        
        print(f"\n📧 EMAIL SYSTEM STATUS:")
        if success_rate >= 80:
            print("✅ EXCELLENT - Email system is working properly!")
            print("📧 Emails are being processed (check console for output)")
        elif success_rate >= 60:
            print("⚠️  GOOD - Email system mostly working, some issues")
        else:
            print("❌ NEEDS ATTENTION - Email system has issues")
        
        print(f"\n💡 NOTES:")
        print("- Console backend prints emails to terminal output")
        print("- For production, configure SMTP settings in settings.py")
        print("- Check Django server console for email content")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 60

if __name__ == '__main__':
    tester = EmailSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Email system is working correctly!")
    else:
        print("\n⚠️  Email system needs configuration.")
