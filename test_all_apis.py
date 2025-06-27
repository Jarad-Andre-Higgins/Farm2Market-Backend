#!/usr/bin/env python
"""
Comprehensive API Testing Script for Farm2Market
Tests all available API endpoints
"""
import requests
import json
import sys
from datetime import datetime

class Farm2MarketAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.authenticated = False
        
    def log_test(self, endpoint, method, status_code, success, message=""):
        """Log test results"""
        result = {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'success': success,
            'message': message,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {method} {endpoint} - {status_code} - {message}")
        
    def test_get_endpoint(self, endpoint, description, headers=None):
        """Test GET endpoint"""
        try:
            url = f"{self.api_url}{endpoint}"
            response = self.session.get(url, headers=headers, timeout=10)
            success = response.status_code in [200, 201]
            message = description
            if not success:
                try:
                    error_data = response.json()
                    message = f"{description} - {error_data.get('error', 'Unknown error')}"
                except:
                    message = f"{description} - HTTP {response.status_code}"
            
            self.log_test(endpoint, "GET", response.status_code, success, message)
            return response
        except Exception as e:
            self.log_test(endpoint, "GET", 0, False, f"{description} - {str(e)}")
            return None

    def authenticate(self):
        """Authenticate and get token"""
        try:
            # Try to login with test credentials using general auth endpoint
            login_data = {
                'email': 'testbuyer@buyer.com',
                'password': 'buyer123'
            }

            response = requests.post(f"{self.api_url}/auth/login/", json=login_data)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('token'):
                    self.auth_token = data['token']
                    self.authenticated = True
                    print(f"✅ Authentication successful! Token: {self.auth_token[:20]}...")
                    return True

            # Fallback to buyer-specific login
            response = requests.post(f"{self.api_url}/buyer/login/", json=login_data)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('token'):
                    self.auth_token = data['token']
                    self.authenticated = True
                    print(f"✅ Authentication successful (fallback)! Token: {self.auth_token[:20]}...")
                    return True

            print("❌ Authentication failed")
            return False

        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_post_endpoint(self, endpoint, data, description, headers=None):
        """Test POST endpoint"""
        try:
            url = f"{self.api_url}{endpoint}"
            if headers is None:
                headers = {'Content-Type': 'application/json'}
            
            response = self.session.post(url, json=data, headers=headers, timeout=10)
            success = response.status_code in [200, 201]
            message = description
            if not success:
                try:
                    error_data = response.json()
                    message = f"{description} - {error_data.get('error', 'Unknown error')}"
                except:
                    message = f"{description} - HTTP {response.status_code}"
            
            self.log_test(endpoint, "POST", response.status_code, success, message)
            return response
        except Exception as e:
            self.log_test(endpoint, "POST", 0, False, f"{description} - {str(e)}")
            return None

    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🧪 FARM2MARKET API COMPREHENSIVE TESTING")
        print("=" * 60)
        print(f"Testing API at: {self.api_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. Test API Root
        print("\n📋 1. API ROOT & BASIC ENDPOINTS")
        self.test_get_endpoint("/", "API Root - Shows available endpoints")
        
        # 2. Test Categories
        print("\n📂 2. CATEGORIES API")
        self.test_get_endpoint("/categories/", "Get all product categories")
        
        # 3. Test Search APIs
        print("\n🔍 3. SEARCH APIs")
        self.test_get_endpoint("/search/?q=tomato", "Search products for 'tomato'")
        self.test_get_endpoint("/search/?q=farm&type=farmer", "Search farmers for 'farm'")
        self.test_get_endpoint("/search/farmers/", "Search farmers endpoint")
        
        # 4. Test Product APIs
        print("\n🌾 4. PRODUCT APIs")
        self.test_get_endpoint("/products/", "Get all products")
        self.test_get_endpoint("/products/1/", "Get product details (ID: 1)")
        
        # 5. Test Public Listings
        print("\n📋 5. PUBLIC LISTINGS")
        self.test_get_endpoint("/farmer/1/listings/", "Get farmer listings (ID: 1)")
        self.test_get_endpoint("/urgent-sales/public/", "Get public urgent sales")
        
        # 6. Test Authentication APIs
        print("\n🔐 6. AUTHENTICATION APIs")
        
        # Test buyer registration
        buyer_data = {
            "username": "testbuyer123",
            "email": "testbuyer@example.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "Buyer",
            "phone": "1234567890"
        }
        response = self.test_post_endpoint("/buyer/register/", buyer_data, "Buyer registration")
        
        # Test buyer login
        login_data = {
            "email": "testbuyer@example.com",
            "password": "testpass123"
        }
        response = self.test_post_endpoint("/buyer/login/", login_data, "Buyer login")
        
        # Extract token if login successful
        if response and response.status_code in [200, 201]:
            try:
                data = response.json()
                if data.get('success') and data.get('token'):
                    self.auth_token = data['token']
                    print(f"🔑 Authentication token obtained: {self.auth_token[:20]}...")
            except:
                pass
        
        # 7. Test Protected Endpoints (with authentication)
        print("\n🔒 7. PROTECTED ENDPOINTS (Require Authentication)")

        # Authenticate first
        if not self.authenticated:
            print("🔐 Authenticating for protected endpoints...")
            self.authenticate()

        auth_headers = {}
        if self.auth_token:
            auth_headers = {'Authorization': f'Token {self.auth_token}'}
        
        self.test_get_endpoint("/buyer/profile/", "Get buyer profile", auth_headers)
        self.test_get_endpoint("/buyer/dashboard-data/", "Get buyer dashboard data", auth_headers)
        self.test_get_endpoint("/notifications/", "Get user notifications", auth_headers)
        self.test_get_endpoint("/messages/conversations/", "Get user conversations", auth_headers)
        self.test_get_endpoint("/messages/unread-count/", "Get unread messages count", auth_headers)
        
        # 8. Test Farmer-specific endpoints
        print("\n🚜 8. FARMER ENDPOINTS")
        self.test_get_endpoint("/farmer/listings/", "Get farmer listings (requires farmer auth)", auth_headers)
        self.test_get_endpoint("/farmer/reservations/", "Get farmer reservations", auth_headers)
        self.test_get_endpoint("/farmer/urgent-sales/", "Get farmer urgent sales", auth_headers)
        self.test_get_endpoint("/farmer/profile/", "Get farmer profile", auth_headers)
        self.test_get_endpoint("/farmer/dashboard/", "Get farmer dashboard data", auth_headers)
        
        # 9. Test Admin endpoints
        print("\n👑 9. ADMIN ENDPOINTS")
        self.test_get_endpoint("/admin/pending-farmers/", "Get pending farmers (admin only)", auth_headers)
        
        # 10. Test Reservation APIs
        print("\n📅 10. RESERVATION APIs")
        reservation_data = {
            "listing_id": 1,
            "quantity": 5,
            "delivery_method": "pickup"
        }
        self.test_post_endpoint("/reservations/create/", reservation_data, "Create reservation", auth_headers)
        
        # Print Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['method']} {result['endpoint']} - {result['message']}")
        
        print(f"\n🎯 API ENDPOINTS TESTED:")
        unique_endpoints = set([r['endpoint'] for r in self.test_results])
        for endpoint in sorted(unique_endpoints):
            print(f"  • {endpoint}")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function"""
    print("🚀 Starting Farm2Market API Tests...")
    
    tester = Farm2MarketAPITester()
    tester.run_all_tests()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
