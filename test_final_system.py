#!/usr/bin/env python
"""
Final Comprehensive System Test for Agriport
Tests all components: Admin, Farmer, Buyer, APIs, Database
"""
import requests
import json
import os
from datetime import datetime

class AgriportFinalTester:
    def __init__(self):
        self.api_url = "http://localhost:8000/api"
        self.admin_token = None
        self.farmer_token = None
        self.buyer_token = None
        self.test_results = []
        
    def log_test(self, category, test_name, success, message=""):
        """Log test results"""
        result = {
            'category': category,
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {category} - {test_name}: {message}")
    
    def test_admin_system(self):
        """Test complete admin system"""
        print("\n🔐 TESTING ADMIN SYSTEM")
        print("-" * 50)
        
        # Admin login
        try:
            response = requests.post(f"{self.api_url}/admin/login/", json={
                'email': 'admin@agriport.com',
                'password': 'admin123'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.admin_token = data['token']
                    self.log_test("Admin", "Login", True, "Admin authentication successful")
                else:
                    self.log_test("Admin", "Login", False, "Login failed")
                    return False
            else:
                self.log_test("Admin", "Login", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin", "Login", False, f"Error: {str(e)}")
            return False
        
        # Admin dashboard
        try:
            response = requests.get(f"{self.api_url}/admin/dashboard/", headers={
                'Authorization': f'Token {self.admin_token}'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stats = data.get('dashboard_data', {}).get('system_stats', {})
                    self.log_test("Admin", "Dashboard", True, 
                        f"Dashboard loaded - {stats.get('total_users', 0)} users")
                else:
                    self.log_test("Admin", "Dashboard", False, "Dashboard failed")
            else:
                self.log_test("Admin", "Dashboard", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Admin", "Dashboard", False, f"Error: {str(e)}")
        
        # User management
        try:
            response = requests.get(f"{self.api_url}/admin/manage-users/", headers={
                'Authorization': f'Token {self.admin_token}'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    users = data.get('users', [])
                    self.log_test("Admin", "User Management", True, 
                        f"Retrieved {len(users)} users")
                else:
                    self.log_test("Admin", "User Management", False, "Failed to get users")
            else:
                self.log_test("Admin", "User Management", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Admin", "User Management", False, f"Error: {str(e)}")
        
        return True
    
    def test_farmer_system(self):
        """Test farmer system"""
        print("\n🚜 TESTING FARMER SYSTEM")
        print("-" * 50)
        
        # Farmer login
        try:
            response = requests.post(f"{self.api_url}/auth/login/", json={
                'email': 'testfarmer@farm.com',
                'password': 'farmer123'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.farmer_token = data['token']
                    self.log_test("Farmer", "Login", True, "Farmer authentication successful")
                else:
                    self.log_test("Farmer", "Login", False, "Login failed")
                    return False
            else:
                self.log_test("Farmer", "Login", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Farmer", "Login", False, f"Error: {str(e)}")
            return False
        
        # Farmer profile
        try:
            response = requests.get(f"{self.api_url}/farmer/profile/", headers={
                'Authorization': f'Token {self.farmer_token}'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Farmer", "Profile", True, "Profile loaded successfully")
                else:
                    self.log_test("Farmer", "Profile", False, "Profile failed")
            else:
                self.log_test("Farmer", "Profile", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Farmer", "Profile", False, f"Error: {str(e)}")
        
        # Farmer listings
        try:
            response = requests.get(f"{self.api_url}/farmer/listings/", headers={
                'Authorization': f'Token {self.farmer_token}'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    listings = data.get('listings', [])
                    self.log_test("Farmer", "Listings", True, 
                        f"Retrieved {len(listings)} listings")
                else:
                    self.log_test("Farmer", "Listings", False, "Failed to get listings")
            else:
                self.log_test("Farmer", "Listings", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Farmer", "Listings", False, f"Error: {str(e)}")
        
        return True
    
    def test_buyer_system(self):
        """Test buyer system"""
        print("\n🛒 TESTING BUYER SYSTEM")
        print("-" * 50)
        
        # Buyer login
        try:
            response = requests.post(f"{self.api_url}/auth/login/", json={
                'email': 'testbuyer@buyer.com',
                'password': 'buyer123'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.buyer_token = data['token']
                    self.log_test("Buyer", "Login", True, "Buyer authentication successful")
                else:
                    self.log_test("Buyer", "Login", False, "Login failed")
                    return False
            else:
                self.log_test("Buyer", "Login", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Buyer", "Login", False, f"Error: {str(e)}")
            return False
        
        # Buyer profile
        try:
            response = requests.get(f"{self.api_url}/buyer/profile/", headers={
                'Authorization': f'Token {self.buyer_token}'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Buyer", "Profile", True, "Profile loaded successfully")
                else:
                    self.log_test("Buyer", "Profile", False, "Profile failed")
            else:
                self.log_test("Buyer", "Profile", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Buyer", "Profile", False, f"Error: {str(e)}")
        
        # Buyer dashboard
        try:
            response = requests.get(f"{self.api_url}/buyer/dashboard-data/", headers={
                'Authorization': f'Token {self.buyer_token}'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Buyer", "Dashboard", True, "Dashboard loaded successfully")
                else:
                    self.log_test("Buyer", "Dashboard", False, "Dashboard failed")
            else:
                self.log_test("Buyer", "Dashboard", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Buyer", "Dashboard", False, f"Error: {str(e)}")
        
        return True
    
    def test_public_apis(self):
        """Test public APIs"""
        print("\n🌐 TESTING PUBLIC APIS")
        print("-" * 50)
        
        # API Root
        try:
            response = requests.get(f"{self.api_url}/")
            if response.status_code == 200:
                self.log_test("Public", "API Root", True, "API root accessible")
            else:
                self.log_test("Public", "API Root", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Public", "API Root", False, f"Error: {str(e)}")
        
        # Categories
        try:
            response = requests.get(f"{self.api_url}/categories/")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    categories = data.get('categories', [])
                    self.log_test("Public", "Categories", True, 
                        f"Retrieved {len(categories)} categories")
                else:
                    self.log_test("Public", "Categories", False, "Categories failed")
            else:
                self.log_test("Public", "Categories", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Public", "Categories", False, f"Error: {str(e)}")
        
        # Products
        try:
            response = requests.get(f"{self.api_url}/products/")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    products = data.get('products', [])
                    self.log_test("Public", "Products", True, 
                        f"Retrieved {len(products)} products")
                else:
                    self.log_test("Public", "Products", False, "Products failed")
            else:
                self.log_test("Public", "Products", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Public", "Products", False, f"Error: {str(e)}")
        
        # Search
        try:
            response = requests.get(f"{self.api_url}/search/?q=tomato")
            if response.status_code == 200:
                self.log_test("Public", "Search", True, "Search functionality working")
            else:
                self.log_test("Public", "Search", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Public", "Search", False, f"Error: {str(e)}")
    
    def test_frontend_files(self):
        """Test frontend file structure"""
        print("\n📁 TESTING FRONTEND FILES")
        print("-" * 50)
        
        base_path = "C:/Users/LENOVO T570/Documents/augment-projects/farm2market/Frontend"
        
        # Admin files
        admin_files = ['admin_login.html', 'admin_dashboard.html', 'admin_dashboard.js']
        admin_path = os.path.join(base_path, 'Admin')
        
        missing_admin = []
        for file in admin_files:
            if not os.path.exists(os.path.join(admin_path, file)):
                missing_admin.append(file)
        
        if not missing_admin:
            self.log_test("Frontend", "Admin Files", True, f"All {len(admin_files)} admin files exist")
        else:
            self.log_test("Frontend", "Admin Files", False, f"Missing: {', '.join(missing_admin)}")
        
        # Farmer files
        farmer_files = ['loginfarmer.html', 'dashboardfarmer.html']
        farmer_path = os.path.join(base_path, 'Farmer')
        
        missing_farmer = []
        for file in farmer_files:
            if not os.path.exists(os.path.join(farmer_path, file)):
                missing_farmer.append(file)
        
        if not missing_farmer:
            self.log_test("Frontend", "Farmer Files", True, f"All {len(farmer_files)} farmer files exist")
        else:
            self.log_test("Frontend", "Farmer Files", False, f"Missing: {', '.join(missing_farmer)}")
        
        # Buyer files
        buyer_files = ['loginbuyer.html', 'dashboardbuyer.html']
        buyer_path = os.path.join(base_path, 'Buyer')
        
        missing_buyer = []
        for file in buyer_files:
            if not os.path.exists(os.path.join(buyer_path, file)):
                missing_buyer.append(file)
        
        if not missing_buyer:
            self.log_test("Frontend", "Buyer Files", True, f"All {len(buyer_files)} buyer files exist")
        else:
            self.log_test("Frontend", "Buyer Files", False, f"Missing: {', '.join(missing_buyer)}")
    
    def run_final_test(self):
        """Run complete system test"""
        print("🚀 AGRIPORT FINAL SYSTEM TESTING")
        print("=" * 80)
        print(f"Testing complete Agriport system at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Run all test categories
        self.test_admin_system()
        self.test_farmer_system()
        self.test_buyer_system()
        self.test_public_apis()
        self.test_frontend_files()
        
        # Generate comprehensive summary
        print("\n" + "=" * 80)
        print("📊 AGRIPORT FINAL SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        # Categorize results
        categories = {}
        for result in self.test_results:
            category = result['category']
            if category not in categories:
                categories[category] = {'total': 0, 'passed': 0}
            categories[category]['total'] += 1
            if result['success']:
                categories[category]['passed'] += 1
        
        # Display category results
        total_tests = len(self.test_results)
        total_passed = sum(1 for r in self.test_results if r['success'])
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 CATEGORY BREAKDOWN:")
        for category, stats in categories.items():
            success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
            print(f"  {status} {category}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {total_passed}")
        print(f"❌ Failed: {total_tests - total_passed}")
        print(f"Success Rate: {overall_success_rate:.1f}%")
        
        # System status
        print(f"\n🎯 AGRIPORT SYSTEM STATUS:")
        if overall_success_rate >= 95:
            print("🌟 EXCELLENT - Agriport is production-ready!")
            print("   All systems operational, ready for deployment")
        elif overall_success_rate >= 85:
            print("✅ VERY GOOD - Agriport is nearly production-ready")
            print("   Minor issues that can be addressed post-deployment")
        elif overall_success_rate >= 75:
            print("⚠️  GOOD - Agriport has some issues to address")
            print("   Most functionality works, some improvements needed")
        elif overall_success_rate >= 60:
            print("⚠️  FAIR - Agriport needs attention")
            print("   Core functionality works but significant issues exist")
        else:
            print("❌ POOR - Agriport needs major fixes")
            print("   Multiple critical issues need resolution")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['category']} - {test['test_name']}: {test['message']}")
        
        print(f"\n⏰ Testing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return overall_success_rate >= 85

if __name__ == '__main__':
    tester = AgriportFinalTester()
    success = tester.run_final_test()
    
    if success:
        print("\n🎉 AGRIPORT IS READY FOR HOSTING AND DEPLOYMENT!")
        print("🚀 The system is production-ready with comprehensive functionality")
    else:
        print("\n⚠️  AGRIPORT NEEDS SOME ATTENTION BEFORE DEPLOYMENT")
        print("🔧 Please address the failed tests before hosting")
