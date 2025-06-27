from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    CustomUser, FarmerProfile, BuyerProfile, Category,
    FarmerListing, ProductCategory, Reservation, UrgentSale,
    UrgentSaleReservation, Transaction, Notification, Review,
    Conversation, Message, MessageReadStatus, EmailVerificationToken,
    PasswordResetToken
)

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password_confirm', 'user_type', 'phone_number', 'first_name', 'last_name']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")

        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Note: Profiles are created in the specific registration views
        # to allow for additional data like location

        return user

class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('User account is disabled.')
            else:
                raise serializers.ValidationError('Invalid email or password.')
        else:
            raise serializers.ValidationError('Must include email and password.')
        
        return data

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for categories"""
    class Meta:
        model = Category
        fields = ['category_id', 'name']

class FarmerListingSerializer(serializers.ModelSerializer):
    """Serializer for farmer listings"""
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    farmer_name = serializers.CharField(source='farmer.username', read_only=True)
    
    class Meta:
        model = FarmerListing
        fields = [
            'listing_id', 'farmer', 'farmer_name', 'product_name', 'description', 
            'price', 'quantity', 'quantity_unit', 'image_url', 'status', 
            'created_at', 'categories', 'category_ids'
        ]
        read_only_fields = ['listing_id', 'farmer', 'created_at']
    
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        listing = FarmerListing.objects.create(**validated_data)
        
        # Add categories
        for category_id in category_ids:
            try:
                category = Category.objects.get(category_id=category_id)
                ProductCategory.objects.create(listing=listing, category=category)
            except Category.DoesNotExist:
                pass
        
        return listing

class ReservationSerializer(serializers.ModelSerializer):
    """Serializer for reservations"""
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    buyer_phone = serializers.CharField(source='buyer.phone_number', read_only=True)
    product_name = serializers.CharField(source='listing.product_name', read_only=True)
    farmer_name = serializers.CharField(source='listing.farmer.username', read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'reservation_id', 'buyer', 'buyer_name', 'buyer_phone',
            'listing', 'product_name', 'farmer_name', 'quantity', 
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reservation_id', 'created_at', 'updated_at']
    
    def validate(self, data):
        listing = data.get('listing')
        quantity = data.get('quantity')
        
        if listing and quantity:
            if quantity > listing.quantity:
                raise serializers.ValidationError(f"Requested quantity ({quantity}) exceeds available quantity ({listing.quantity})")
            
            if listing.status != 'Available':
                raise serializers.ValidationError("Product is not available for reservation")
        
        return data

class UrgentSaleSerializer(serializers.ModelSerializer):
    """Serializer for urgent sales"""
    farmer_name = serializers.CharField(source='farmer.username', read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = UrgentSale
        fields = [
            'urgent_sale_id', 'farmer', 'farmer_name', 'product_name', 'description',
            'original_price', 'reduced_price', 'discount_percentage', 'quantity', 
            'quantity_unit', 'best_before', 'reason', 'image_url', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['urgent_sale_id', 'farmer', 'created_at', 'updated_at']
    
    def get_discount_percentage(self, obj):
        if obj.original_price > 0:
            return round(((obj.original_price - obj.reduced_price) / obj.original_price) * 100, 2)
        return 0

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    class Meta:
        model = Notification
        fields = ['notification_id', 'user', 'title', 'message', 'notification_type', 'is_read', 'created_at', 'read_at']
        read_only_fields = ['notification_id', 'created_at', 'read_at']

class FarmerProfileSerializer(serializers.ModelSerializer):
    """Serializer for farmer profiles"""
    username = serializers.CharField(source='farmer.username', read_only=True)
    email = serializers.CharField(source='farmer.email', read_only=True)
    phone_number = serializers.CharField(source='farmer.phone_number', read_only=True)
    first_name = serializers.CharField(source='farmer.first_name')
    last_name = serializers.CharField(source='farmer.last_name')
    
    class Meta:
        model = FarmerProfile
        fields = ['farmer', 'username', 'email', 'phone_number', 'first_name', 'last_name', 'location', 'trust_badge']
        read_only_fields = ['farmer', 'trust_badge']
    
    def update(self, instance, validated_data):
        # Update user fields
        user_data = {}
        if 'farmer' in validated_data:
            farmer_data = validated_data.pop('farmer')
            for key, value in farmer_data.items():
                user_data[key] = value
        
        if user_data:
            for key, value in user_data.items():
                setattr(instance.farmer, key, value)
            instance.farmer.save()
        
        # Update profile fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        
        return instance

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions"""
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    farmer_name = serializers.CharField(source='farmer.username', read_only=True)
    product_name = serializers.CharField(source='reservation.listing.product_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'reservation', 'buyer', 'buyer_name',
            'farmer', 'farmer_name', 'product_name', 'payment_method',
            'receipt_url', 'status', 'created_at'
        ]
        read_only_fields = ['transaction_id', 'created_at']


# Chat Serializers
class MessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    sender_type = serializers.CharField(source='sender.user_type', read_only=True)

    class Meta:
        model = Message
        fields = [
            'message_id', 'conversation', 'sender', 'sender_name', 'sender_type',
            'content', 'status', 'created_at', 'read_at'
        ]
        read_only_fields = ['message_id', 'created_at', 'read_at']


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for chat conversations"""
    participants = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'conversation_id', 'participants', 'last_message',
            'unread_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['conversation_id', 'created_at', 'updated_at']

    def get_participants(self, obj):
        """Get participant details"""
        participants = []
        for user in obj.participants.all():
            participants.append({
                'id': user.id,
                'name': user.username,
                'user_type': user.user_type,
                'avatar': None,  # Add avatar field when implemented
                'isOnline': False  # Add online status when implemented
            })
        return participants

    def get_last_message(self, obj):
        """Get the last message in the conversation"""
        last_message = obj.get_last_message()
        if last_message:
            return {
                'id': last_message.message_id,
                'senderId': last_message.sender.id,
                'content': last_message.content,
                'timestamp': last_message.created_at,
                'status': last_message.status
            }
        return None

    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        request = self.context.get('request')
        if request and request.user:
            # Count messages not read by current user
            return obj.messages.exclude(
                read_statuses__user=request.user
            ).exclude(sender=request.user).count()
        return 0


class ConversationCreateSerializer(serializers.Serializer):
    """Serializer for creating new conversations"""
    recipient_id = serializers.IntegerField()

    def validate_recipient_id(self, value):
        """Validate that recipient exists and is different from sender"""
        try:
            recipient = CustomUser.objects.get(id=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Recipient not found")

        request = self.context.get('request')
        if request and request.user.id == value:
            raise serializers.ValidationError("Cannot start conversation with yourself")

        return value


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new messages"""

    class Meta:
        model = Message
        fields = ['conversation', 'content']

    def validate_conversation(self, value):
        """Validate that user is participant in the conversation"""
        request = self.context.get('request')
        if request and request.user not in value.participants.all():
            raise serializers.ValidationError("You are not a participant in this conversation")
        return value


# Buyer Authentication Serializers
class BuyerRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for buyer registration"""
    password_confirm = serializers.CharField(write_only=True, required=False)
    location = serializers.CharField(max_length=100, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'password_confirm', 'location']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }

    def validate_email(self, value):
        """Validate email uniqueness"""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone_number(self, value):
        """Validate phone number format for Cameroon"""
        import re
        # Accept various formats: +237123456789, 237123456789, 123456789
        if value and not re.match(r'^(\+?237)?[1-9]\d{8}$', value):
            raise serializers.ValidationError("Please enter a valid phone number (e.g., +237123456789).")
        return value

    def create(self, validated_data):
        """Create buyer user with auto-generated password"""
        import secrets
        import string
        from django.utils import timezone
        from datetime import timedelta

        # Remove location from user data
        location = validated_data.pop('location', '')
        validated_data.pop('password_confirm', None)

        # Generate secure password
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

        # Create user
        user = CustomUser.objects.create_user(
            username=validated_data['email'],  # Use email as username
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number', ''),
            user_type='Buyer',
            password=password,
            is_approved=True  # Buyers are auto-approved
        )

        # Create buyer profile
        BuyerProfile.objects.create(
            buyer=user,
            location=location
        )

        # Create email verification token
        token = secrets.token_urlsafe(32)
        EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24)
        )

        # Store password for email sending
        user._generated_password = password
        user._verification_token = token

        return user


class BuyerLoginSerializer(serializers.Serializer):
    """Serializer for buyer login"""
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        """Validate login credentials"""
        email = data.get('email')
        password = data.get('password')

        if email and password:
            try:
                user = CustomUser.objects.get(email=email, user_type='Buyer')
                if not user.check_password(password):
                    raise serializers.ValidationError("Invalid email or password.")
                if not user.is_approved:
                    raise serializers.ValidationError("Your account is pending approval.")
                data['user'] = user
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            raise serializers.ValidationError("Email and password are required.")

        return data


class BuyerProfileSerializer(serializers.ModelSerializer):
    """Serializer for buyer profile"""
    user_email = serializers.CharField(source='buyer.email', read_only=True)
    user_name = serializers.CharField(source='buyer.get_full_name', read_only=True)
    user_phone = serializers.CharField(source='buyer.phone_number', read_only=True)

    class Meta:
        model = BuyerProfile
        fields = [
            'location', 'preferred_delivery_method', 'delivery_address',
            'avatar', 'date_of_birth', 'delivery_time_preferences',
            'email_notifications', 'sms_notifications', 'marketing_emails',
            'user_email', 'user_name', 'user_phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate that user exists"""
        try:
            user = CustomUser.objects.get(email=value, user_type='Buyer')
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No buyer account found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate(self, data):
        """Validate password reset data"""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")

        # Validate token
        try:
            reset_token = PasswordResetToken.objects.get(
                token=data['token'],
                is_used=False
            )
            if reset_token.is_expired():
                raise serializers.ValidationError("Password reset token has expired.")
            data['reset_token'] = reset_token
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid password reset token.")

        return data


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    token = serializers.CharField()

    def validate_token(self, value):
        """Validate verification token"""
        try:
            verification_token = EmailVerificationToken.objects.get(
                token=value,
                is_used=False
            )
            if verification_token.is_expired():
                raise serializers.ValidationError("Email verification token has expired.")
            return value
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid email verification token.")
