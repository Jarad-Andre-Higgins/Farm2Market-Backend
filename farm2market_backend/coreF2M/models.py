from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import secrets
import re

def validate_minimum_age(value):
    """Validate that user is at least 13 years old"""
    if value and (timezone.now().date() - value).days < 13 * 365:
        raise ValidationError("User must be at least 13 years old")

class CustomUser(AbstractUser):
    """Custom User model with comprehensive constraints"""
    USER_TYPE_CHOICES = [
        ('Farmer', 'Farmer'),
        ('Buyer', 'Buyer'),
        ('Admin', 'Admin'),
    ]

    # Email with strict validation
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message="Enter a valid email address")],
        help_text="Must be a valid, unique email address"
    )

    # Phone number with validation
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{1,14}$',
                message="Phone number must be in format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )

    # User type with strict choices
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        help_text="User role in the system"
    )

    # Approval status
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether the user account has been approved by admin"
    )

    # Override username to use email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'user_type']

    class Meta:
        db_table = 'users_customuser'
        constraints = [
            # Ensure email is lowercase
            models.CheckConstraint(
                check=models.Q(email__exact=models.F('email__lower')),
                name='email_lowercase'
            ),
            # Ensure user_type is valid
            models.CheckConstraint(
                check=models.Q(user_type__in=['Farmer', 'Buyer', 'Admin']),
                name='valid_user_type'
            ),
            # Ensure first_name and last_name are not empty if provided
            models.CheckConstraint(
                check=models.Q(first_name__isnull=True) | ~models.Q(first_name__exact=''),
                name='first_name_not_empty'
            ),
            models.CheckConstraint(
                check=models.Q(last_name__isnull=True) | ~models.Q(last_name__exact=''),
                name='last_name_not_empty'
            ),
        ]
        indexes = [
            models.Index(fields=['user_type', 'is_approved'], name='user_type_approved_idx'),
            models.Index(fields=['email'], name='email_idx'),
            models.Index(fields=['is_active', 'user_type'], name='active_user_type_idx'),
        ]

    def clean(self):
        """Custom validation"""
        super().clean()

        # Ensure email is lowercase
        if self.email:
            self.email = self.email.lower()

        # Validate user type specific requirements
        if self.user_type == 'Admin' and not self.is_staff:
            self.is_staff = True

        # Ensure username is unique and not empty
        if not self.username or self.username.strip() == '':
            raise ValidationError("Username cannot be empty")

    def save(self, *args, **kwargs):
        """Override save to ensure data integrity"""
        self.full_clean()
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        """Override to remove password uniqueness check"""
        super().set_password(raw_password)

class FarmerProfile(models.Model):
    """Farmer profile with comprehensive constraints"""
    farmer = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='farmer_id',
        limit_choices_to={'user_type': 'Farmer'}
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s,.-]+$',
                message="Location can only contain letters, spaces, commas, periods, and hyphens"
            )
        ]
    )
    trust_badge = models.BooleanField(
        default=False,
        help_text="Indicates if farmer has earned trust badge"
    )

    class Meta:
        db_table = 'farmer_profiles'
        constraints = [
            # Ensure location is not empty if provided
            models.CheckConstraint(
                check=models.Q(location__isnull=True) | ~models.Q(location__exact=''),
                name='farmer_location_not_empty'
            ),
        ]

    def clean(self):
        """Custom validation for farmer profile"""
        super().clean()
        if self.farmer and self.farmer.user_type != 'Farmer':
            raise ValidationError("Profile can only be created for Farmer users")

class BuyerProfile(models.Model):
    """Enhanced buyer profile with strict constraints"""
    DELIVERY_CHOICES = [
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('both', 'Both')
    ]

    buyer = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='buyer_id',
        limit_choices_to={'user_type': 'Buyer'}
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s,.-]+$',
                message="Location can only contain letters, spaces, commas, periods, and hyphens"
            )
        ]
    )
    preferred_delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES,
        default='pickup'
    )
    delivery_address = models.TextField(
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s,.-]+$',
                message="Address can only contain letters, numbers, spaces, commas, periods, and hyphens"
            )
        ]
    )
    avatar = models.URLField(blank=True, null=True)
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        validators=[validate_minimum_age]
    )

    class Meta:
        db_table = 'buyer_profiles'
        constraints = [
            # Ensure location is not empty if provided
            models.CheckConstraint(
                check=models.Q(location__isnull=True) | ~models.Q(location__exact=''),
                name='buyer_location_not_empty'
            ),
            # Ensure delivery address is provided if delivery method includes delivery
            models.CheckConstraint(
                check=models.Q(preferred_delivery_method='pickup') |
                      ~models.Q(delivery_address__isnull=True),
                name='delivery_address_required'
            ),
        ]

    def clean(self):
        """Custom validation for buyer profile"""
        super().clean()
        if self.buyer and self.buyer.user_type != 'Buyer':
            raise ValidationError("Profile can only be created for Buyer users")

        if self.preferred_delivery_method in ['delivery', 'both'] and not self.delivery_address:
            raise ValidationError("Delivery address is required when delivery method includes delivery")

    # Delivery preferences
    delivery_time_preferences = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Comma-separated delivery time preferences"
    )

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    marketing_emails = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Buyer Profile: {self.buyer.username}"


class EmailVerificationToken(models.Model):
    """Email verification tokens for user registration"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, db_column='user_id')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'email_verification_tokens'

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Email verification for {self.user.email}"


class PasswordResetToken(models.Model):
    """Password reset tokens"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column='user_id')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_tokens'

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Password reset for {self.user.email}"

class Category(models.Model):
    """Farmer-controlled product categories with admin approval"""
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    category_id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s&-]+$',
                message="Category name can only contain letters, spaces, ampersands, and hyphens"
            )
        ]
    )
    description = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Description of the category"
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'Farmer'},
        help_text="Farmer who created this category"
    )
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending'
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_categories',
        limit_choices_to={'user_type': 'Admin'},
        help_text="Admin who approved this category"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        constraints = [
            # Ensure category name is not empty
            models.CheckConstraint(
                check=~models.Q(name__exact=''),
                name='category_name_not_empty'
            ),
            # Ensure unique category name per farmer
            models.UniqueConstraint(
                fields=['name', 'created_by'],
                name='unique_category_per_farmer'
            ),
        ]
        indexes = [
            models.Index(fields=['name'], name='category_name_idx'),
            models.Index(fields=['created_by', 'approval_status'], name='farmer_category_status_idx'),
            models.Index(fields=['approval_status'], name='category_approval_idx'),
        ]

    def clean(self):
        """Custom validation for category"""
        super().clean()
        if self.name:
            # Ensure proper title case
            self.name = self.name.title()
            # Remove extra spaces
            self.name = ' '.join(self.name.split())

        if self.approval_status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()

    def save(self, *args, **kwargs):
        """Override save to ensure data integrity"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (by {self.created_by.username}) - {self.approval_status}"

    def __str__(self):
        return self.name

class FarmerListing(models.Model):
    """Farmer product listings with comprehensive constraints"""
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Sold', 'Sold'),
        ('Reserved', 'Reserved'),
    ]

    UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('g', 'Grams'),
        ('basket', 'Basket'),
        ('bag', 'Bag'),
        ('cartoon', 'Cartoon'),
        ('piece', 'Piece'),
        ('bunch', 'Bunch'),
        ('liter', 'Liter'),
    ]

    listing_id = models.AutoField(primary_key=True)
    farmer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        db_column='farmer_id',
        limit_choices_to={'user_type': 'Farmer', 'is_approved': True}
    )
    product_name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z\s&-]+$',
                message="Product name can only contain letters, spaces, ampersands, and hyphens"
            )
        ]
    )
    description = models.TextField(
        blank=True,
        null=True,
        max_length=1000,
        help_text="Product description (max 1000 characters)"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01, message="Price must be greater than 0")]
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1, message="Quantity must be at least 1")]
    )
    quantity_unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default='kg'
    )
    image_url = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Available'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'farmer_listings'
        constraints = [
            # Ensure product name is not empty
            models.CheckConstraint(
                check=~models.Q(product_name__exact=''),
                name='product_name_not_empty'
            ),
            # Ensure price is positive
            models.CheckConstraint(
                check=models.Q(price__gt=0),
                name='price_positive'
            ),
            # Ensure quantity is positive
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name='quantity_positive'
            ),
            # Ensure valid status
            models.CheckConstraint(
                check=models.Q(status__in=['Available', 'Sold', 'Reserved']),
                name='valid_listing_status'
            ),
        ]
        indexes = [
            models.Index(fields=['farmer', 'status'], name='farmer_status_idx'),
            models.Index(fields=['status', 'created_at'], name='status_created_idx'),
            models.Index(fields=['product_name'], name='product_name_idx'),
        ]

    def clean(self):
        """Custom validation for farmer listing"""
        super().clean()

        if self.farmer and self.farmer.user_type != 'Farmer':
            raise ValidationError("Only farmers can create listings")

        if self.farmer and not self.farmer.is_approved:
            raise ValidationError("Only approved farmers can create listings")

        if self.product_name:
            # Ensure proper title case
            self.product_name = self.product_name.title()

    def save(self, *args, **kwargs):
        """Override save to ensure data integrity"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} by {self.farmer.username}"

class ProductCategory(models.Model):
    """Many-to-many relationship between products and categories with constraints"""
    listing = models.ForeignKey(FarmerListing, on_delete=models.CASCADE, db_column='listing_id')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_id')

    class Meta:
        db_table = 'product_categories'
        unique_together = ('listing', 'category')
        constraints = [
            # Ensure no duplicate category assignments
            models.UniqueConstraint(
                fields=['listing', 'category'],
                name='unique_listing_category'
            ),
        ]
        indexes = [
            models.Index(fields=['listing'], name='product_category_listing_idx'),
            models.Index(fields=['category'], name='product_category_category_idx'),
        ]

    def __str__(self):
        return f"{self.listing.product_name} - {self.category.name}"

class Reservation(models.Model):
    """Enhanced buyer reservations for farmer products"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('payment_pending', 'Payment Pending'),
        ('paid', 'Paid'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    DELIVERY_METHOD_CHOICES = [
        ('pickup', 'Pickup from Farmer'),
        ('delivery', 'Home Delivery'),
    ]

    reservation_id = models.AutoField(primary_key=True)
    buyer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        db_column='buyer_id',
        related_name='buyer_reservations',
        limit_choices_to={'user_type': 'Buyer', 'is_approved': True}
    )
    listing = models.ForeignKey(FarmerListing, on_delete=models.CASCADE, db_column='listing_id')

    # Reservation details with validation
    quantity = models.IntegerField(
        validators=[MinValueValidator(1, message="Quantity must be at least 1")]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.01, message="Unit price must be greater than 0")]
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.01, message="Total amount must be greater than 0")]
    )

    # Delivery information
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES, default='pickup')
    delivery_address = models.TextField(
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9\s,.-]+$',
                message="Address can only contain letters, numbers, spaces, commas, periods, and hyphens"
            )
        ]
    )
    preferred_pickup_date = models.DateTimeField(null=True, blank=True)
    preferred_delivery_date = models.DateTimeField(null=True, blank=True)

    # Status and notes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    buyer_notes = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Buyer notes (max 500 characters)"
    )
    farmer_notes = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Farmer notes (max 500 characters)"
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Reason for rejection (max 500 characters)"
    )

    # Approval tracking
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_reservations',
        limit_choices_to={'user_type__in': ['Farmer', 'Admin']}
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Reservation expiry

    class Meta:
        db_table = 'reservations'
        ordering = ['-created_at']
        constraints = [
            # Ensure quantity is positive
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name='reservation_quantity_positive'
            ),
            # Ensure unit price is positive
            models.CheckConstraint(
                check=models.Q(unit_price__gt=0),
                name='reservation_unit_price_positive'
            ),
            # Ensure total amount is positive
            models.CheckConstraint(
                check=models.Q(total_amount__gt=0),
                name='reservation_total_amount_positive'
            ),
            # Ensure delivery address is provided for delivery method
            models.CheckConstraint(
                check=models.Q(delivery_method='pickup') |
                      ~models.Q(delivery_address__isnull=True),
                name='delivery_address_required_for_delivery'
            ),
            # Ensure valid status
            models.CheckConstraint(
                check=models.Q(status__in=[
                    'pending', 'approved', 'rejected', 'payment_pending',
                    'paid', 'ready_for_pickup', 'completed', 'cancelled'
                ]),
                name='valid_reservation_status'
            ),
        ]
        indexes = [
            models.Index(fields=['buyer', 'status'], name='buyer_status_idx'),
            models.Index(fields=['listing', 'status'], name='listing_status_idx'),
            models.Index(fields=['status', 'created_at'], name='reservation_status_created_idx'),
            models.Index(fields=['approved_by'], name='approved_by_idx'),
        ]

    def clean(self):
        """Custom validation for reservation"""
        super().clean()

        if self.buyer and self.buyer.user_type != 'Buyer':
            raise ValidationError("Only buyers can create reservations")

        if self.buyer and not self.buyer.is_approved:
            raise ValidationError("Only approved buyers can create reservations")

        if self.delivery_method == 'delivery' and not self.delivery_address:
            raise ValidationError("Delivery address is required for delivery method")

        if self.quantity and self.unit_price:
            calculated_total = self.quantity * self.unit_price
            if abs(self.total_amount - calculated_total) > 0.01:  # Allow for small rounding differences
                self.total_amount = calculated_total

        if self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()

        if self.status == 'rejected' and not self.rejection_reason:
            raise ValidationError("Rejection reason is required when rejecting a reservation")

    def save(self, *args, **kwargs):
        """Override save to ensure data integrity"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reservation {self.reservation_id} - {self.listing.product_name}"

    def approve(self, farmer, notes=""):
        """Farmer approves the reservation"""
        self.status = 'approved'
        self.approved_by = farmer
        self.approved_at = timezone.now()
        self.farmer_notes = notes
        self.save()

    def reject(self, farmer, reason=""):
        """Farmer rejects the reservation"""
        self.status = 'rejected'
        self.approved_by = farmer
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()

    def calculate_total(self):
        """Calculate total amount"""
        self.total_amount = self.quantity * self.unit_price
        return self.total_amount

class UrgentSale(models.Model):
    """Urgent sales with discounted prices"""
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Reserved', 'Reserved'),
        ('Sold', 'Sold'),
    ]

    urgent_sale_id = models.AutoField(primary_key=True)
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column='farmer_id')
    product_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    reduced_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    quantity_unit = models.CharField(max_length=20, default='kg')
    best_before = models.DateField()
    reason = models.TextField()
    image_url = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Available')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'urgent_sales'

    def __str__(self):
        return f"Urgent: {self.product_name} by {self.farmer.username}"

class UrgentSaleReservation(models.Model):
    """Reservations for urgent sales"""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    reservation_id = models.AutoField(primary_key=True)
    urgent_sale = models.ForeignKey(UrgentSale, on_delete=models.CASCADE, db_column='urgent_sale_id')
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column='buyer_id')
    quantity = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'urgent_sale_reservations'

class Transaction(models.Model):
    """Purchase transactions with receipt upload system"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash Payment'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('receipt_uploaded', 'Receipt Uploaded'),
        ('receipt_verified', 'Receipt Verified'),
        ('receipt_rejected', 'Receipt Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    transaction_id = models.AutoField(primary_key=True)
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, db_column='reservation_id')
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column='buyer_id', related_name='buyer_transactions')
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column='farmer_id', related_name='farmer_transactions')

    # Payment details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')

    # Receipt upload system
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    receipt_url = models.URLField(max_length=500, blank=True, null=True)  # Alternative to image field
    receipt_notes = models.TextField(blank=True, null=True)  # Buyer's notes about payment

    # Farmer verification
    farmer_verification_notes = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_transactions')
    verified_at = models.DateTimeField(null=True, blank=True)

    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')

    # Delivery information
    delivery_method = models.CharField(
        max_length=20,
        choices=[('pickup', 'Pickup'), ('delivery', 'Delivery')],
        default='pickup'
    )
    delivery_address = models.TextField(blank=True, null=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.reservation.listing.product_name}"

    def verify_receipt(self, farmer, notes=""):
        """Farmer verifies the uploaded receipt"""
        self.status = 'receipt_verified'
        self.verified_by = farmer
        self.verified_at = timezone.now()
        self.farmer_verification_notes = notes
        self.save()

    def reject_receipt(self, farmer, notes=""):
        """Farmer rejects the uploaded receipt"""
        self.status = 'receipt_rejected'
        self.verified_by = farmer
        self.verified_at = timezone.now()
        self.farmer_verification_notes = notes
        self.save()

    def complete_transaction(self):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

class Notification(models.Model):
    """Enhanced user notifications with proper categorization"""
    NOTIFICATION_TYPE_CHOICES = [
        ('reservation_approved', 'Reservation Approved'),
        ('reservation_rejected', 'Reservation Rejected'),
        ('reservation_pending', 'Reservation Pending'),
        ('new_message', 'New Message'),
        ('product_available', 'Product Available'),
        ('urgent_sale', 'Urgent Sale'),
        ('payment_received', 'Payment Received'),
        ('receipt_uploaded', 'Receipt Uploaded'),
        ('receipt_verified', 'Receipt Verified'),
        ('system_announcement', 'System Announcement'),
    ]

    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
    ]

    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column='user_id')
    title = models.CharField(max_length=200, default="Notification")
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES, default='system_announcement')
    is_read = models.BooleanField(default=False)

    # Optional references to related objects
    reservation = models.ForeignKey('Reservation', on_delete=models.CASCADE, null=True, blank=True)
    transaction = models.ForeignKey('Transaction', on_delete=models.CASCADE, null=True, blank=True)
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, null=True, blank=True)

    # Metadata
    data = models.JSONField(default=dict, blank=True)  # Additional notification data

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

class Review(models.Model):
    """Buyer reviews for farmers"""
    review_id = models.AutoField(primary_key=True)
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column='buyer_id', related_name='buyer_reviews')
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column='farmer_id', related_name='farmer_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], blank=True, null=True)
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'

    def __str__(self):
        return f"Review by {self.buyer.username} for {self.farmer.username}"


class Conversation(models.Model):
    """Enhanced chat conversations between farmers and buyers"""
    CONVERSATION_TYPE_CHOICES = [
        ('direct', 'Direct Message'),
        ('product_inquiry', 'Product Inquiry'),
        ('reservation_discussion', 'Reservation Discussion'),
        ('support', 'Customer Support'),
    ]

    conversation_id = models.AutoField(primary_key=True)
    participants = models.ManyToManyField(CustomUser, related_name='conversations')

    # Conversation metadata
    conversation_type = models.CharField(max_length=30, choices=CONVERSATION_TYPE_CHOICES, default='direct')
    title = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Related objects (optional)
    related_listing = models.ForeignKey('FarmerListing', on_delete=models.SET_NULL, null=True, blank=True)
    related_reservation = models.ForeignKey('Reservation', on_delete=models.SET_NULL, null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'conversations'
        ordering = ['-last_message_at', '-updated_at']

    def __str__(self):
        participant_names = ", ".join([user.username for user in self.participants.all()])
        return f"Conversation between {participant_names}"

    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        return self.participants.exclude(id=user.id).first()

    def get_last_message(self):
        """Get the most recent message in this conversation"""
        return self.messages.order_by('-created_at').first()

    def update_last_message_time(self):
        """Update the last message timestamp"""
        last_message = self.get_last_message()
        if last_message:
            self.last_message_at = last_message.created_at
            self.save(update_fields=['last_message_at'])

    def get_unread_count_for_user(self, user):
        """Get count of unread messages for a specific user"""
        return self.messages.exclude(sender=user).exclude(
            read_statuses__user=user
        ).count()

    def mark_all_as_read_for_user(self, user):
        """Mark all messages in conversation as read for a user"""
        unread_messages = self.messages.exclude(sender=user).exclude(
            read_statuses__user=user
        )

        for message in unread_messages:
            MessageReadStatus.objects.get_or_create(
                message=message,
                user=user
            )


class Message(models.Model):
    """Individual messages within conversations"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]

    message_id = models.AutoField(primary_key=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', db_column='conversation_id')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages', db_column='sender_id')
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username}: {self.content[:50]}..."

    def mark_as_read(self):
        """Mark message as read"""
        if self.status != 'read':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()


class MessageReadStatus(models.Model):
    """Track read status of messages for each participant"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_statuses', db_column='message_id')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column='user_id')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message_read_status'
        unique_together = ['message', 'user']

    def __str__(self):
        return f"{self.user.username} read message {self.message.message_id}"


class FileUpload(models.Model):
    """File upload management for receipts, images, etc."""
    FILE_TYPE_CHOICES = [
        ('receipt', 'Payment Receipt'),
        ('product_image', 'Product Image'),
        ('profile_image', 'Profile Image'),
        ('document', 'Document'),
        ('other', 'Other'),
    ]

    file_id = models.AutoField(primary_key=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column='uploaded_by_id')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()  # Size in bytes
    mime_type = models.CharField(max_length=100)

    # Optional references
    related_transaction = models.ForeignKey('Transaction', on_delete=models.CASCADE, null=True, blank=True)
    related_listing = models.ForeignKey('FarmerListing', on_delete=models.CASCADE, null=True, blank=True)

    # Metadata
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_files')
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'file_uploads'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.file_name} ({self.file_type})"


class SystemConfiguration(models.Model):
    """System-wide configuration settings"""
    config_key = models.CharField(max_length=100, unique=True, primary_key=True)
    config_value = models.TextField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_configuration'

    def __str__(self):
        return f"{self.config_key}: {self.config_value[:50]}"


class AuditLog(models.Model):
    """Audit log for tracking important system actions"""
    ACTION_TYPE_CHOICES = [
        ('user_registration', 'User Registration'),
        ('user_login', 'User Login'),
        ('reservation_created', 'Reservation Created'),
        ('reservation_approved', 'Reservation Approved'),
        ('transaction_created', 'Transaction Created'),
        ('receipt_uploaded', 'Receipt Uploaded'),
        ('receipt_verified', 'Receipt Verified'),
        ('message_sent', 'Message Sent'),
        ('admin_action', 'Admin Action'),
    ]

    log_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    # Optional references to related objects
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.PositiveIntegerField(blank=True, null=True)

    # Additional data
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        user_info = self.user.username if self.user else "Anonymous"
        return f"{self.action_type} by {user_info} at {self.created_at}"


class AdminRole(models.Model):
    """Admin role definitions for role-based access control"""
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('user_manager', 'User Manager'),
        ('transaction_manager', 'Transaction Manager'),
        ('content_moderator', 'Content Moderator'),
        ('analytics_viewer', 'Analytics Viewer'),
        ('support_agent', 'Support Agent'),
    ]

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    permissions = models.JSONField(default=dict)  # Store permissions as JSON
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'admin_roles'

    def __str__(self):
        return self.display_name


class AdminRoleAssignment(models.Model):
    """Assign roles to admin users"""
    admin_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'Admin'},
        related_name='role_assignments'
    )
    role = models.ForeignKey(AdminRole, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='role_assignments_made',
        limit_choices_to={'user_type': 'Admin'}
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'admin_role_assignments'
        unique_together = ['admin_user', 'role']

    def __str__(self):
        return f"{self.admin_user.username} - {self.role.display_name}"
