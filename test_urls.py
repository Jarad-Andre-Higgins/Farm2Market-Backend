#!/usr/bin/env python
"""
Test script to verify URL accessibility
"""
import requests
import sys

def test_url(url, description):
    """Test if a URL is accessible"""
    try:
        response = requests.get(url, timeout=5)
        status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
        print(f"{status} - {description}: {url}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ERROR - {description}: {url} - {str(e)}")
        return False

def main():
    """Test all important URLs"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Farm2Market URLs...")
    print("=" * 50)
    
    tests = [
        (f"{base_url}/", "Home Page"),
        (f"{base_url}/admin/", "Admin Panel"),
        (f"{base_url}/api/", "API Root"),
        (f"{base_url}/buyer-dashboard.html", "Buyer Dashboard"),
        (f"{base_url}/buyer-login.html", "Buyer Login"),
        (f"{base_url}/buyer-signup.html", "Buyer Signup"),
        (f"{base_url}/farmer-dashboard.html", "Farmer Dashboard"),
        (f"{base_url}/loginfarmer.html", "Farmer Login"),
    ]
    
    passed = 0
    total = len(tests)
    
    for url, description in tests:
        if test_url(url, description):
            passed += 1
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Farm2Market server is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the server configuration.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
