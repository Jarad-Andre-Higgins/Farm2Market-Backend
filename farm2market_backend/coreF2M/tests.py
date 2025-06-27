from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal
import json

from .models import (
    CustomUser, FarmerProfile, BuyerProfile, Category,
    FarmerListing, ProductCategory, Reservation, Transaction,
    Notification, Conversation, Message, MessageReadStatus,
    FileUpload, SystemConfiguration, AuditLog
)

User = get_user_model()


class ModelTestCase(TestCase):
    """Test all model functionality"""

    def setUp(self):
        """Set up test data"""
        # Create test users
        self.farmer = CustomUser.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123',
            user_type='Farmer',
            first_name='Test',
            last_name='Farmer',
            is_approved=True
        )

        self.buyer = CustomUser.objects.create_user(
            username='testbuyer',
            email='buyer@test.com',
            password='testpass123',
            user_type='Buyer',
            first_name='Test',
            last_name='Buyer',
            is_approved=True
        )

        # Create profiles
        self.farmer_profile = FarmerProfile.objects.create(
            farmer=self.farmer,
            location='Test Farm Location',
            trust_badge=True
        )

        self.buyer_profile = BuyerProfile.objects.create(
            buyer=self.buyer,
            location='Test Buyer Location',
            preferred_delivery_method='delivery'
        )

        # Create category
        self.category = Category.objects.create(name='Test Vegetables')

        # Create listing
        self.listing = FarmerListing.objects.create(
            farmer=self.farmer,
            product_name='Test Tomatoes',
            description='Fresh test tomatoes',
            price=Decimal('5.00'),
            quantity=100,
            quantity_unit='kg'
        )

        # Link category to listing
        ProductCategory.objects.create(
            listing=self.listing,
            category=self.category
        )

    def test_user_creation(self):
        """Test user model creation"""
        self.assertEqual(self.farmer.user_type, 'Farmer')
        self.assertEqual(self.buyer.user_type, 'Buyer')
        self.assertTrue(self.farmer.is_approved)
        self.assertTrue(self.buyer.is_approved)

    def test_profile_creation(self):
        """Test profile model creation"""
        self.assertEqual(self.farmer_profile.farmer, self.farmer)
        self.assertEqual(self.buyer_profile.buyer, self.buyer)
        self.assertTrue(self.farmer_profile.trust_badge)

    def test_listing_creation(self):
        """Test listing model creation"""
        self.assertEqual(self.listing.farmer, self.farmer)
        self.assertEqual(self.listing.product_name, 'Test Tomatoes')
        self.assertEqual(self.listing.price, Decimal('5.00'))

    def test_reservation_workflow(self):
        """Test reservation creation and workflow"""
        reservation = Reservation.objects.create(
            buyer=self.buyer,
            listing=self.listing,
            quantity=10,
            unit_price=self.listing.price,
            total_amount=Decimal('50.00'),
            delivery_method='pickup'
        )

        self.assertEqual(reservation.status, 'pending')
        self.assertEqual(reservation.total_amount, Decimal('50.00'))

        # Test approval
        reservation.approve(self.farmer, "Approved for pickup")
        self.assertEqual(reservation.status, 'approved')
        self.assertEqual(reservation.approved_by, self.farmer)

    def test_transaction_workflow(self):
        """Test transaction and receipt workflow"""
        # Create reservation first
        reservation = Reservation.objects.create(
            buyer=self.buyer,
            listing=self.listing,
            quantity=5,
            unit_price=self.listing.price,
            total_amount=Decimal('25.00')
        )

        # Create transaction
        transaction = Transaction.objects.create(
            reservation=reservation,
            buyer=self.buyer,
            farmer=self.farmer,
            total_amount=Decimal('25.00'),
            payment_method='cash'
        )

        self.assertEqual(transaction.status, 'pending_payment')

        # Test receipt verification
        transaction.verify_receipt(self.farmer, "Payment confirmed")
        self.assertEqual(transaction.status, 'receipt_verified')
        self.assertEqual(transaction.verified_by, self.farmer)

    def test_conversation_and_messaging(self):
        """Test chat functionality"""
        # Create conversation
        conversation = Conversation.objects.create(
            conversation_type='product_inquiry',
            title='Test Chat'
        )
        conversation.participants.add(self.farmer, self.buyer)

        # Test message creation
        message = Message.objects.create(
            conversation=conversation,
            sender=self.buyer,
            content='Hello, interested in your tomatoes!'
        )

        self.assertEqual(message.sender, self.buyer)
        self.assertEqual(message.status, 'sent')

        # Test conversation methods
        other_participant = conversation.get_other_participant(self.buyer)
        self.assertEqual(other_participant, self.farmer)

        last_message = conversation.get_last_message()
        self.assertEqual(last_message, message)

    def test_notification_system(self):
        """Test notification creation and management"""
        notification = Notification.objects.create(
            user=self.buyer,
            title='Test Notification',
            message='This is a test notification',
            notification_type='system_announcement'
        )

        self.assertFalse(notification.is_read)

        # Test mark as read
        notification.mark_as_read()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)


class APITestCase(APITestCase):
    """Test API endpoints"""

    def setUp(self):
        """Set up test data for API tests"""
        self.client = APIClient()

        # Create test users
        self.farmer = CustomUser.objects.create_user(
            username='apifarmer',
            email='apifarmer@test.com',
            password='testpass123',
            user_type='Farmer',
            first_name='API',
            last_name='Farmer',
            is_approved=True
        )

        self.buyer = CustomUser.objects.create_user(
            username='apibuyer',
            email='apibuyer@test.com',
            password='testpass123',
            user_type='Buyer',
            first_name='API',
            last_name='Buyer',
            is_approved=True
        )

        # Create tokens
        self.farmer_token = Token.objects.create(user=self.farmer)
        self.buyer_token = Token.objects.create(user=self.buyer)

        # Create profiles
        FarmerProfile.objects.create(farmer=self.farmer, location='API Farm')
        BuyerProfile.objects.create(buyer=self.buyer, location='API Buyer Location')

        # Create test data
        self.category = Category.objects.create(name='API Vegetables')
        self.listing = FarmerListing.objects.create(
            farmer=self.farmer,
            product_name='API Tomatoes',
            price=Decimal('3.00'),
            quantity=50
        )

    def test_buyer_authentication(self):
        """Test buyer login API"""
        url = reverse('login_buyer')
        data = {
            'email': 'apibuyer@test.com',
            'password': 'testpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('token', response.data)

    def test_categories_api(self):
        """Test categories API"""
        url = reverse('categories_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('categories', response.data)

    def test_products_api(self):
        """Test products API"""
        url = reverse('get_all_products')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('products', response.data)

    def test_chat_api_authenticated(self):
        """Test chat API with authentication"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.buyer_token.key)

        # Test get conversations
        url = reverse('get_conversations')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('conversations', response.data)

    def test_start_conversation_api(self):
        """Test starting a conversation"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.buyer_token.key)

        url = reverse('start_conversation')
        data = {
            'recipient_id': self.farmer.id,
            'initial_message': 'Hello farmer!',
            'conversation_type': 'product_inquiry'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('conversation_id', response.data)

    def test_unauthorized_access(self):
        """Test that protected endpoints require authentication"""
        url = reverse('get_conversations')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
