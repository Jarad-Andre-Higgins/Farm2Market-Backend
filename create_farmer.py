#!/usr/bin/env python
"""
Create farmer user for testing
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import CustomUser, FarmerProfile
from rest_framework.authtoken.models import Token

def create_farmer():
    # Delete existing farmer if exists
    try:
        existing = CustomUser.objects.get(email='testfarmer@agriport.com')
        existing.delete()
        print("Deleted existing farmer")
    except CustomUser.DoesNotExist:
        pass
    
    # Create farmer user
    farmer = CustomUser.objects.create_user(
        email='testfarmer@agriport.com',
        username='testfarmer2024',
        password='farmer123',
        user_type='Farmer',
        first_name='Test',
        last_name='Farmer',
        is_approved=True,
        is_active=True
    )
    
    # Create farmer profile
    FarmerProfile.objects.create(farmer=farmer, location='Test Location')
    
    # Create token
    token, created = Token.objects.get_or_create(user=farmer)
    
    print(f"✅ Created farmer: {farmer.email}")
    print(f"✅ Token: {token.key}")
    
    return farmer, token.key

if __name__ == '__main__':
    create_farmer()
