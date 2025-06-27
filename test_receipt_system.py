#!/usr/bin/env python
"""
Test the receipt upload system
"""
import requests
import json
import os
import sys
import django

# Set up Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import *

def create_test_transaction():
    """Create a test transaction for testing receipt upload"""
    try:
        # Get test buyer and farmer
        buyer = CustomUser.objects.get(email='testbuyer@buyer.com')
        farmer = CustomUser.objects.get(email='testfarmer@farm.com')
        
        # Get a test listing
        listing = FarmerListing.objects.first()
        if not listing:
            print("❌ No listings found. Please run simple_test_data.py first")
            return None
        
        # Create reservation
        reservation = Reservation.objects.create(
            buyer=buyer,
            listing=listing,
            quantity=5,
            unit_price=listing.price,
            total_amount=5 * listing.price,
            delivery_method='pickup',
            status='approved'
        )
        
        # Create transaction
        transaction = Transaction.objects.create(
            reservation=reservation,
            buyer=buyer,
            farmer=farmer,
            total_amount=reservation.total_amount,
            payment_method='cash',
            status='pending_payment'
        )
        
        print(f"✅ Created test transaction ID: {transaction.transaction_id}")
        return transaction.transaction_id
        
    except Exception as e:
        print(f"❌ Error creating test transaction: {e}")
        return None

def test_receipt_system():
    """Test receipt upload and verification system"""
    base_url = "http://localhost:8000/api"
    
    print("📄 TESTING RECEIPT UPLOAD SYSTEM")
    print("=" * 50)
    
    # Create test transaction
    transaction_id = create_test_transaction()
    if not transaction_id:
        return
    
    # Login as buyer
    print("\n1. Logging in as buyer...")
    login_data = {
        "email": "testbuyer@buyer.com",
        "password": "buyer123"
    }
    
    response = requests.post(f"{base_url}/buyer/login/", json=login_data)
    if response.status_code == 200:
        buyer_token = response.json()['token']
        buyer_headers = {'Authorization': f'Token {buyer_token}'}
        print(f"✅ Buyer login successful!")
    else:
        print(f"❌ Buyer login failed: {response.text}")
        return
    
    # Test 1: Upload receipt (without file for now)
    print("\n2. Testing receipt upload...")
    try:
        receipt_data = {
            "transaction_id": transaction_id,
            "receipt_notes": "Paid in cash at the farm. Receipt attached."
        }
        
        response = requests.post(f"{base_url}/transactions/upload-receipt/", 
                               data=receipt_data, headers=buyer_headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Receipt uploaded successfully!")
        else:
            print(f"❌ Failed to upload receipt")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Login as farmer
    print("\n3. Logging in as farmer...")
    farmer_login_data = {
        "email": "testfarmer@farm.com",
        "password": "farmer123"
    }
    
    # We need to create a farmer login endpoint or use the general login
    # For now, let's test with the buyer token and see what happens
    
    # Test 2: Verify receipt (approve)
    print("\n4. Testing receipt verification...")
    try:
        verify_data = {
            "action": "approve",
            "notes": "Receipt verified. Payment confirmed."
        }
        
        # Note: This will fail because we're using buyer token, but let's see the error
        response = requests.post(f"{base_url}/transactions/{transaction_id}/verify-receipt/", 
                               json=verify_data, headers=buyer_headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Receipt verified successfully!")
        else:
            print(f"❌ Failed to verify receipt (expected - need farmer token)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 Receipt system testing completed!")
    print("Note: Full testing requires farmer authentication endpoint")

if __name__ == '__main__':
    test_receipt_system()
