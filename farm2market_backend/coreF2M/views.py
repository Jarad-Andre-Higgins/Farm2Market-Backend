from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views.generic import TemplateView
import logging
import os

logger = logging.getLogger(__name__)
from .email_utils import (
    send_buyer_welcome_email, send_password_reset_email,
    send_email_verification, send_reservation_status_update_email,
    send_farmer_registration_email, send_farmer_approval_email,
    send_system_notification_email, send_admin_broadcast_email
)
from .models import (
    CustomUser, FarmerProfile, BuyerProfile, Category,
    FarmerListing, ProductCategory, Reservation, UrgentSale,
    UrgentSaleReservation, Transaction, Notification, Review,
    Conversation, Message, MessageReadStatus, EmailVerificationToken,
    PasswordResetToken, FileUpload, SystemConfiguration, AuditLog
)
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, CategorySerializer,
    FarmerListingSerializer, ReservationSerializer, UrgentSaleSerializer,
    NotificationSerializer, FarmerProfileSerializer, TransactionSerializer,
    ConversationSerializer, MessageSerializer, ConversationCreateSerializer,
    MessageCreateSerializer, BuyerRegistrationSerializer, BuyerLoginSerializer,
    BuyerProfileSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    EmailVerificationSerializer
)

# API Root View
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_root(request):
    """API Root endpoint showing available endpoints"""
    return Response({
        'message': 'Farm2Market API',
        'version': '1.0',
        'status': 'operational',
        'endpoints': {
            'authentication': {
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'buyer_register': '/api/buyer/register/',
                'buyer_login': '/api/buyer/login/',
                'farmer_register': '/api/farmer/register/',
                'farmer_login': '/api/farmer/login/',
            },
            'products': {
                'list': '/api/products/',
                'search': '/api/search/',
                'farmer_listings': '/api/farmer/listings/',
            },
            'reservations': {
                'create': '/api/reservations/',
                'farmer_reservations': '/api/farmer/reservations/',
            },
            'profiles': {
                'buyer_profile': '/api/buyer/profile/',
                'farmer_profile': '/api/farmer/profile/',
            },
            'categories': '/api/categories/',
        }
    })

# Authentication Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """Register a new user (farmer or buyer)"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Different handling for farmers vs buyers
        if user.user_type == 'Farmer':
            # Farmers need admin approval - don't create token yet
            # Send notification to admin
            admin_users = CustomUser.objects.filter(user_type='Admin', is_active=True)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title="New Farmer Registration",
                    message=f"New farmer registration: {user.username} ({user.email}) requires approval.",
                    notification_type="system_announcement"
                )

            # Send confirmation email to farmer
            send_farmer_registration_email(user)

            return Response({
                'success': True,
                'message': 'Registration submitted successfully. Your account is pending admin approval. You will receive an email once approved.',
                'user_id': user.id,
                'user_type': user.user_type,
                'email': user.email,
                'requires_approval': True
            }, status=status.HTTP_201_CREATED)
        else:
            # Buyers are auto-approved
            user.is_approved = True
            user.save()
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                'success': True,
                'message': 'User registered successfully',
                'user_id': user.id,
                'user_type': user.user_type,
                'token': token.key,
                'email': user.email,
                'requires_approval': False
            }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    """Login user and return token"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']

        # Check if farmer is approved
        if user.user_type == 'Farmer' and not user.is_approved:
            return Response({
                'success': False,
                'message': 'Your farmer account is pending admin approval. Please wait for approval email.',
                'requires_approval': True
            }, status=status.HTTP_403_FORBIDDEN)

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'success': True,
            'message': 'Login successful',
            'user_id': user.id,
            'user_type': user.user_type,
            'token': token.key,
            'email': user.email,
            'username': user.username,
            'is_approved': user.is_approved
        }, status=status.HTTP_200_OK)
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

# Category Views
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def categories_list(request):
    """Get all approved categories for public use"""
    try:
        # Only show approved categories to public
        categories = Category.objects.filter(approval_status='approved').order_by('name')
        categories_data = []

        for category in categories:
            categories_data.append({
                'category_id': category.category_id,
                'name': category.name,
                'description': category.description,
                'created_by': category.created_by.username,
                'created_at': category.created_at.isoformat()
            })

        return Response({
            'success': True,
            'categories': categories_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch categories'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def farmer_categories(request):
    """Manage farmer's categories"""
    if not request.user.user_type == 'Farmer':
        return Response({
            'success': False,
            'error': 'Only farmers can manage categories'
        }, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Get farmer's categories
        try:
            categories = Category.objects.filter(created_by=request.user).order_by('-created_at')
            categories_data = []

            for category in categories:
                categories_data.append({
                    'category_id': category.category_id,
                    'name': category.name,
                    'description': category.description,
                    'approval_status': category.approval_status,
                    'created_at': category.created_at.isoformat(),
                    'approved_at': category.approved_at.isoformat() if category.approved_at else None,
                    'can_edit': category.approval_status in ['pending', 'rejected'],
                    'can_delete': not category.productcategory_set.exists()
                })

            return Response({
                'success': True,
                'categories': categories_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching farmer categories: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch categories'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        # Create new category
        try:
            data = request.data
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()

            if not name:
                return Response({
                    'success': False,
                    'error': 'Category name is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if farmer already has a category with this name
            if Category.objects.filter(created_by=request.user, name__iexact=name).exists():
                return Response({
                    'success': False,
                    'error': 'You already have a category with this name'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create category
            category = Category.objects.create(
                name=name,
                description=description,
                created_by=request.user,
                approval_status='pending'
            )

            # Notify admins
            admin_users = CustomUser.objects.filter(user_type='Admin', is_active=True)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title="New Category Request",
                    message=f"Farmer {request.user.username} requested a new category: {name}",
                    notification_type="category_request"
                )

            return Response({
                'success': True,
                'message': 'Category created and submitted for approval',
                'category': {
                    'category_id': category.category_id,
                    'name': category.name,
                    'description': category.description,
                    'approval_status': category.approval_status,
                    'created_at': category.created_at.isoformat()
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating category: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to create category'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def farmer_category_detail(request, category_id):
    """Update or delete farmer's category"""
    if not request.user.user_type == 'Farmer':
        return Response({
            'success': False,
            'error': 'Only farmers can manage categories'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        category = Category.objects.get(category_id=category_id, created_by=request.user)
    except Category.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Category not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        # Update category
        try:
            data = request.data
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()

            if not name:
                return Response({
                    'success': False,
                    'error': 'Category name is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if farmer already has another category with this name
            existing = Category.objects.filter(
                created_by=request.user,
                name__iexact=name
            ).exclude(category_id=category_id)

            if existing.exists():
                return Response({
                    'success': False,
                    'error': 'You already have a category with this name'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update category
            category.name = name
            category.description = description
            category.approval_status = 'pending'  # Reset to pending after edit
            category.approved_by = None
            category.approved_at = None
            category.save()

            return Response({
                'success': True,
                'message': 'Category updated and resubmitted for approval',
                'category': {
                    'category_id': category.category_id,
                    'name': category.name,
                    'description': category.description,
                    'approval_status': category.approval_status,
                    'created_at': category.created_at.isoformat()
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error updating category: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to update category'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'DELETE':
        # Delete category
        try:
            # Check if category is being used in any listings
            if category.productcategory_set.exists():
                return Response({
                    'success': False,
                    'error': 'Cannot delete category that is being used in product listings'
                }, status=status.HTTP_400_BAD_REQUEST)

            category.delete()

            return Response({
                'success': True,
                'message': 'Category deleted successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error deleting category: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to delete category'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Farmer Listing Views
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def farmer_listings(request):
    """Get farmer's listings or create new listing"""
    if request.method == 'GET':
        # Get listings for the authenticated farmer
        if request.user.user_type != 'Farmer':
            return Response({
                'success': False,
                'message': 'Only farmers can view their listings'
            }, status=status.HTTP_403_FORBIDDEN)

        listings = FarmerListing.objects.filter(farmer=request.user)
        serializer = FarmerListingSerializer(listings, many=True)
        return Response({
            'success': True,
            'listings': serializer.data
        })

    elif request.method == 'POST':
        # Create new listing
        if request.user.user_type != 'Farmer':
            return Response({
                'success': False,
                'message': 'Only farmers can create listings'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = FarmerListingSerializer(data=request.data)
        if serializer.is_valid():
            listing = serializer.save(farmer=request.user)
            return Response({
                'success': True,
                'message': 'Product listing created successfully',
                'listing': FarmerListingSerializer(listing).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_farmer_listings(request, farmer_id):
    """Get public listings for a specific farmer (for buyers to view)"""
    try:
        farmer = CustomUser.objects.get(id=farmer_id, user_type='Farmer')
        listings = FarmerListing.objects.filter(farmer=farmer, status='Available')

        # Group by categories
        listings_by_category = {}
        for listing in listings:
            categories = ProductCategory.objects.filter(listing=listing).select_related('category')
            for pc in categories:
                category_name = pc.category.name
                if category_name not in listings_by_category:
                    listings_by_category[category_name] = []
                listings_by_category[category_name].append(FarmerListingSerializer(listing).data)

        return Response({
            'success': True,
            'farmer_name': farmer.username,
            'farmer_location': getattr(farmer.farmerprofile, 'location', ''),
            'listings_by_category': listings_by_category
        })
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Farmer not found'
        }, status=status.HTTP_404_NOT_FOUND)

# Reservation Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_reservation(request):
    """Create a new reservation (buyers only)"""
    if request.user.user_type != 'Buyer':
        return Response({
            'success': False,
            'message': 'Only buyers can create reservations'
        }, status=status.HTTP_403_FORBIDDEN)

    serializer = ReservationSerializer(data=request.data)
    if serializer.is_valid():
        reservation = serializer.save(buyer=request.user)

        # Create notification for farmer
        farmer = reservation.listing.farmer
        Notification.objects.create(
            user=farmer,
            title="New Reservation Request",
            message=f"New reservation request for {reservation.listing.product_name} from {request.user.username}",
            notification_type="reservation_pending"
        )

        return Response({
            'success': True,
            'message': 'Reservation created successfully',
            'reservation': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def farmer_reservations(request):
    """Get all reservations for farmer's products"""
    if request.user.user_type != 'Farmer':
        return Response({
            'success': False,
            'message': 'Only farmers can view reservations'
        }, status=status.HTTP_403_FORBIDDEN)

    # Get reservations for farmer's listings
    farmer_listings = FarmerListing.objects.filter(farmer=request.user)
    reservations = Reservation.objects.filter(listing__in=farmer_listings).order_by('-created_at')

    serializer = ReservationSerializer(reservations, many=True)
    return Response({
        'success': True,
        'reservations': serializer.data
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_reservation_status(request, reservation_id):
    """Update reservation status (approve/reject) - farmers only"""
    if request.user.user_type != 'Farmer':
        return Response({
            'success': False,
            'message': 'Only farmers can update reservation status'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        reservation = Reservation.objects.get(
            reservation_id=reservation_id,
            listing__farmer=request.user
        )

        new_status = request.data.get('status')
        if new_status not in ['Approved', 'Rejected']:
            return Response({
                'success': False,
                'message': 'Invalid status. Use "Approved" or "Rejected"'
            }, status=status.HTTP_400_BAD_REQUEST)

        old_status = reservation.status
        reservation.status = new_status
        reservation.save()

        # Update listing quantity if approved
        if new_status == 'Approved' and old_status == 'Pending':
            listing = reservation.listing
            listing.quantity -= reservation.quantity
            if listing.quantity <= 0:
                listing.status = 'Sold'
            listing.save()

        # Create notification for buyer
        status_message = "approved" if new_status == 'Approved' else "rejected"
        notification_type = "reservation_approved" if new_status == 'Approved' else "reservation_rejected"
        Notification.objects.create(
            user=reservation.buyer,
            title=f"Reservation {status_message.title()}",
            message=f"Your reservation for {reservation.listing.product_name} has been {status_message}",
            notification_type=notification_type
        )

        return Response({
            'success': True,
            'message': f'Reservation {status_message} successfully',
            'reservation': ReservationSerializer(reservation).data
        })

    except Reservation.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Reservation not found'
        }, status=status.HTTP_404_NOT_FOUND)

# Urgent Sale Views
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def urgent_sales(request):
    """Get farmer's urgent sales or create new urgent sale"""
    if request.method == 'GET':
        if request.user.user_type != 'Farmer':
            return Response({
                'success': False,
                'message': 'Only farmers can view their urgent sales'
            }, status=status.HTTP_403_FORBIDDEN)

        urgent_sales = UrgentSale.objects.filter(farmer=request.user)
        serializer = UrgentSaleSerializer(urgent_sales, many=True)
        return Response({
            'success': True,
            'urgent_sales': serializer.data
        })

    elif request.method == 'POST':
        if request.user.user_type != 'Farmer':
            return Response({
                'success': False,
                'message': 'Only farmers can create urgent sales'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = UrgentSaleSerializer(data=request.data)
        if serializer.is_valid():
            urgent_sale = serializer.save(farmer=request.user)
            return Response({
                'success': True,
                'message': 'Urgent sale created successfully',
                'urgent_sale': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_urgent_sales(request):
    """Get all available urgent sales (public view for buyers)"""
    urgent_sales = UrgentSale.objects.filter(status='Available').order_by('-created_at')
    serializer = UrgentSaleSerializer(urgent_sales, many=True)
    return Response({
        'success': True,
        'urgent_sales': serializer.data
    })

# Notification Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_notifications(request):
    """Get user's notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)

    # Count unread notifications
    unread_count = notifications.filter(is_read=False).count()

    return Response({
        'success': True,
        'notifications': serializer.data,
        'unread_count': unread_count
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(
            notification_id=notification_id,
            user=request.user
        )
        notification.status = 'Read'
        notification.save()

        return Response({
            'success': True,
            'message': 'Notification marked as read'
        })
    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)

# Profile Views
@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def farmer_profile(request):
    """Get or update farmer profile"""
    if request.user.user_type != 'Farmer':
        return Response({
            'success': False,
            'message': 'Only farmers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        profile = FarmerProfile.objects.get(farmer=request.user)
    except FarmerProfile.DoesNotExist:
        profile = FarmerProfile.objects.create(farmer=request.user)

    if request.method == 'GET':
        serializer = FarmerProfileSerializer(profile)
        return Response({
            'success': True,
            'profile': serializer.data
        })

    elif request.method == 'PUT':
        serializer = FarmerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'profile': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# Dashboard Data Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def farmer_dashboard_data(request):
    """Get farmer dashboard statistics"""
    if request.user.user_type != 'Farmer':
        return Response({
            'success': False,
            'message': 'Only farmers can access dashboard data'
        }, status=status.HTTP_403_FORBIDDEN)

    # Get farmer's listings
    listings = FarmerListing.objects.filter(farmer=request.user)
    active_listings = listings.filter(status='Available').count()

    # Get pending reservations
    pending_reservations = Reservation.objects.filter(
        listing__farmer=request.user,
        status='Pending'
    ).count()

    # Get recent transactions (this month)
    from django.utils import timezone
    from datetime import datetime, timedelta

    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    transactions = Transaction.objects.filter(
        farmer=request.user,
        status='Successful',
        created_at__gte=current_month
    )

    total_revenue = sum(
        reservation.listing.price * reservation.quantity
        for transaction in transactions
        for reservation in [transaction.reservation]
    )

    # Get unread notifications
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return Response({
        'success': True,
        'dashboard_data': {
            'active_listings': active_listings,
            'pending_reservations': pending_reservations,
            'monthly_revenue': float(total_revenue),
            'unread_notifications': unread_notifications,
            'total_listings': listings.count()
        }
    })

# Search Views
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_farmers(request):
    """Search farmers by location or name"""
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')

    farmers = CustomUser.objects.filter(user_type='Farmer', is_active=True)

    if query:
        farmers = farmers.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    if location:
        farmers = farmers.filter(farmerprofile__location__icontains=location)

    farmer_data = []
    for farmer in farmers:
        try:
            profile = farmer.farmerprofile
            farmer_data.append({
                'farmer_id': farmer.id,
                'username': farmer.username,
                'first_name': farmer.first_name,
                'last_name': farmer.last_name,
                'location': profile.location,
                'trust_badge': profile.trust_badge,
                'active_listings_count': FarmerListing.objects.filter(
                    farmer=farmer,
                    status='Available'
                ).count()
            })
        except FarmerProfile.DoesNotExist:
            continue

    return Response({
        'success': True,
        'farmers': farmer_data
    })

# Email Functions
def send_farmer_registration_email(user):
    """Send confirmation email to farmer after registration"""
    subject = 'Farm2Market - Registration Received'
    message = f"""
Dear {user.first_name or user.username},

Thank you for registering as a farmer on Farm2Market!

Your registration has been received and is currently under review by our admin team.

Registration Details:
- Name: {user.first_name} {user.last_name}
- Email: {user.email}
- Username: {user.username}

What happens next?
1. Our admin team will review your application
2. You will receive an email notification once your account is approved or if additional information is needed
3. Once approved, you can login and start listing your products

This process typically takes 1-2 business days.

If you have any questions, please contact our support team.

Best regards,
Farm2Market Team
    """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send registration email to {user.email}: {e}")


def send_admin_welcome_email(admin_user, password, creator_admin):
    """Send welcome email to newly created admin with login credentials"""
    try:
        subject = '🔐 Welcome to Agriport Admin Panel - Your Account is Ready!'

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2c3e50;">🌱 Welcome to Agriport</h1>
                    <h2 style="color: #e74c3c;">🔐 Administrator Access</h2>
                </div>

                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="color: #27ae60;">Admin Account Created Successfully!</h2>
                    <p>Dear {admin_user.first_name} {admin_user.last_name},</p>
                    <p>Congratulations! Your administrator account has been created by <strong>{creator_admin.first_name} {creator_admin.last_name}</strong> on the Agriport platform.</p>
                    <p>You now have administrative privileges to manage the Agriport agricultural marketplace.</p>
                </div>

                <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #1976d2;">🔑 Your Login Credentials:</h3>
                    <div style="background: #fff; padding: 15px; border-radius: 5px; border-left: 4px solid #2196f3;">
                        <p><strong>Email:</strong> {admin_user.email}</p>
                        <p><strong>Password:</strong> <code style="background: #f5f5f5; padding: 2px 6px; border-radius: 3px;">{password}</code></p>
                        <p><strong>Username:</strong> {admin_user.username}</p>
                        <p><strong>Admin Level:</strong> {'Superuser' if admin_user.is_superuser else 'Standard Admin'}</p>
                    </div>
                </div>

                <div style="background: #fff3cd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #856404;">🚀 Getting Started:</h3>
                    <ol>
                        <li><strong>Login:</strong> Access the admin panel using your credentials above</li>
                        <li><strong>Change Password:</strong> We recommend changing your password after first login</li>
                        <li><strong>Explore Dashboard:</strong> Familiarize yourself with the admin interface</li>
                        <li><strong>Review Permissions:</strong> Understand your administrative privileges</li>
                    </ol>
                </div>

                <div style="background: #d4edda; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #155724;">🛡️ Your Administrative Powers:</h3>
                    <ul>
                        <li>✅ Manage all system users (farmers, buyers, admins)</li>
                        <li>✅ Approve/reject farmer registrations</li>
                        <li>✅ Monitor system activity and analytics</li>
                        <li>✅ Send system announcements</li>
                        <li>✅ View audit logs and system reports</li>
                        {'<li>✅ Create other administrator accounts</li>' if admin_user.is_superuser else ''}
                        {'<li>✅ Full system configuration access</li>' if admin_user.is_superuser else ''}
                    </ul>
                </div>

                <div style="background: #f8d7da; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #721c24;">⚠️ Important Security Notes:</h3>
                    <ul>
                        <li>🔒 Keep your login credentials secure and confidential</li>
                        <li>🔒 Change your password regularly</li>
                        <li>🔒 Never share your admin access with unauthorized persons</li>
                        <li>🔒 Log out properly after each session</li>
                        <li>🔒 Report any suspicious activity immediately</li>
                    </ul>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <div style="background: #2c3e50; color: white; padding: 15px; border-radius: 10px;">
                        <h3>🌟 Welcome to the Agriport Admin Team!</h3>
                        <p>You're now part of the team that helps connect farmers with buyers and grows the agricultural community.</p>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 20px;">
                    <p style="color: #7f8c8d;">If you have any questions, please contact the system administrator.</p>
                    <p style="color: #7f8c8d;"><strong>The Agriport Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_message = f"""
        Welcome to Agriport Admin Panel!

        Dear {admin_user.first_name} {admin_user.last_name},

        Your administrator account has been created by {creator_admin.first_name} {creator_admin.last_name} on the Agriport platform.

        LOGIN CREDENTIALS:
        Email: {admin_user.email}
        Password: {password}
        Username: {admin_user.username}
        Admin Level: {'Superuser' if admin_user.is_superuser else 'Standard Admin'}

        GETTING STARTED:
        1. Login using your credentials above
        2. Change your password after first login
        3. Explore the admin dashboard
        4. Review your administrative privileges

        ADMINISTRATIVE POWERS:
        - Manage all system users (farmers, buyers, admins)
        - Approve/reject farmer registrations
        - Monitor system activity and analytics
        - Send system announcements
        - View audit logs and system reports
        {'- Create other administrator accounts' if admin_user.is_superuser else ''}
        {'- Full system configuration access' if admin_user.is_superuser else ''}

        SECURITY NOTES:
        - Keep your login credentials secure
        - Change your password regularly
        - Never share admin access
        - Log out properly after each session

        Welcome to the Agriport Admin Team!
        The Agriport Team
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [admin_user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return True

    except Exception as e:
        logger.error(f"Failed to send admin welcome email: {str(e)}")
        return False

# Admin API Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def pending_farmers(request):
    """Get list of farmers pending approval (Admin only)"""
    if request.user.user_type != 'Admin':
        return Response({
            'success': False,
            'message': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)

    pending_farmers = CustomUser.objects.filter(
        user_type='Farmer',
        is_approved=False,
        is_active=True
    ).order_by('-date_joined')

    farmers_data = []
    for farmer in pending_farmers:
        try:
            profile = farmer.farmerprofile
            farmers_data.append({
                'user_id': farmer.id,
                'username': farmer.username,
                'email': farmer.email,
                'first_name': farmer.first_name,
                'last_name': farmer.last_name,
                'phone_number': farmer.phone_number,
                'location': profile.location if profile else None,
                'date_joined': farmer.date_joined.isoformat(),
            })
        except FarmerProfile.DoesNotExist:
            farmers_data.append({
                'user_id': farmer.id,
                'username': farmer.username,
                'email': farmer.email,
                'first_name': farmer.first_name,
                'last_name': farmer.last_name,
                'phone_number': farmer.phone_number,
                'location': None,
                'date_joined': farmer.date_joined.isoformat(),
            })

    return Response({
        'success': True,
        'pending_farmers': farmers_data
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_farmer_api(request, farmer_id):
    """Approve farmer via API (Admin only)"""
    if request.user.user_type != 'Admin':
        return Response({
            'success': False,
            'message': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        farmer = CustomUser.objects.get(pk=farmer_id, user_type='Farmer')
        farmer.is_approved = True
        farmer.save()

        # Send approval email
        try:
            send_farmer_approval_email(farmer, approved=True, admin_user=request.user)
            email_sent = True
        except Exception as e:
            logger.error(f"Failed to send farmer approval email: {str(e)}")
            email_sent = False

        # Create notification
        Notification.objects.create(
            user=farmer,
            title="Account Approved!",
            message="Congratulations! Your farmer account has been approved. You can now start listing your products.",
            notification_type="system_announcement"
        )

        return Response({
            'success': True,
            'message': f'Farmer {farmer.username} approved successfully'
        })

    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Farmer not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reject_farmer_api(request, farmer_id):
    """Reject farmer via API (Admin only)"""
    if request.user.user_type != 'Admin':
        return Response({
            'success': False,
            'message': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        farmer = CustomUser.objects.get(pk=farmer_id, user_type='Farmer')

        # Send rejection email
        try:
            send_farmer_approval_email(farmer, approved=False, admin_user=request.user)
            email_sent = True
        except Exception as e:
            logger.error(f"Failed to send farmer rejection email: {str(e)}")
            email_sent = False

        # Create notification
        Notification.objects.create(
            user=farmer,
            title="Account Application Update",
            message="We're sorry, but your farmer account application has been rejected. Please contact support for more information.",
            notification_type="system_announcement"
        )

        # Optionally delete or deactivate
        farmer.is_active = False
        farmer.save()

        return Response({
            'success': True,
            'message': f'Farmer {farmer.username} rejected'
        })

    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Farmer not found'
        }, status=status.HTTP_404_NOT_FOUND)

def send_farmer_approval_email(user, approved=True):
    """Send approval/rejection email to farmer"""
    if approved:
        subject = 'Farm2Market - Account Approved!'
        message = f"""
Dear {user.first_name or user.username},

Congratulations! Your farmer account on Farm2Market has been approved.

You can now:
- Login to your account
- Add your products
- Manage reservations
- Start selling to buyers

Login Details:
Email: {user.email}
Password: [Use the password you created during registration]

Login URL: http://localhost:8000/loginfarmer.html

Welcome to the Farm2Market community!

Best regards,
Farm2Market Team
        """
    else:
        subject = 'Farm2Market - Account Application Update'
        message = f"""
Dear {user.first_name or user.username},

Thank you for your interest in joining Farm2Market as a farmer.

Unfortunately, we cannot approve your account at this time. This could be due to:
- Incomplete information
- Verification requirements not met
- Other administrative reasons

If you believe this is an error or would like to reapply, please contact our support team.

Best regards,
Farm2Market Team
        """

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send approval email to {user.email}: {e}")


# Chat/Messaging Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_conversations(request):
    """Get all conversations for the authenticated user"""
    try:
        conversations = Conversation.objects.filter(
            participants=request.user
        ).order_by('-updated_at')

        serializer = ConversationSerializer(
            conversations,
            many=True,
            context={'request': request}
        )

        return Response({
            'success': True,
            'conversations': serializer.data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def conversation_messages(request, conversation_id):
    """Get all messages in a specific conversation"""
    try:
        conversation = Conversation.objects.get(
            conversation_id=conversation_id,
            participants=request.user
        )

        messages = conversation.messages.all().order_by('created_at')
        serializer = MessageSerializer(messages, many=True)

        # Mark messages as read for the current user
        unread_messages = messages.exclude(sender=request.user).exclude(
            read_statuses__user=request.user
        )

        for message in unread_messages:
            MessageReadStatus.objects.get_or_create(
                message=message,
                user=request.user
            )

        return Response({
            'success': True,
            'messages': serializer.data
        })
    except Conversation.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_message(request):
    """Send a new message in a conversation"""
    try:
        serializer = MessageCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            message = serializer.save(sender=request.user)

            # Update conversation timestamp
            conversation = message.conversation
            conversation.save()  # This will update the updated_at field

            # Create notification for other participants
            other_participants = conversation.participants.exclude(id=request.user.id)
            for participant in other_participants:
                Notification.objects.create(
                    user=participant,
                    title="New Message",
                    message=f"New message from {request.user.username}: {message.content[:50]}...",
                    notification_type="new_message"
                )

            response_serializer = MessageSerializer(message)
            return Response({
                'success': True,
                'message': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_conversation(request):
    """Start a new conversation with another user"""
    try:
        serializer = ConversationCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            recipient_id = serializer.validated_data['recipient_id']
            recipient = CustomUser.objects.get(id=recipient_id)

            # Check if conversation already exists
            existing_conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=recipient
            ).first()

            if existing_conversation:
                response_serializer = ConversationSerializer(
                    existing_conversation,
                    context={'request': request}
                )
                return Response({
                    'success': True,
                    'conversation': response_serializer.data,
                    'existing': True
                })

            # Create new conversation
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, recipient)

            response_serializer = ConversationSerializer(
                conversation,
                context={'request': request}
            )

            return Response({
                'success': True,
                'conversation': response_serializer.data,
                'existing': False
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except CustomUser.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Recipient not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def mark_conversation_read(request, conversation_id):
    """Mark all messages in a conversation as read"""
    try:
        conversation = Conversation.objects.get(
            conversation_id=conversation_id,
            participants=request.user
        )

        # Get unread messages from other participants
        unread_messages = conversation.messages.exclude(sender=request.user).exclude(
            read_statuses__user=request.user
        )

        # Mark all as read
        for message in unread_messages:
            MessageReadStatus.objects.get_or_create(
                message=message,
                user=request.user
            )

        return Response({
            'success': True,
            'message': 'Conversation marked as read'
        })
    except Conversation.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def unread_messages_count(request):
    """Get count of unread messages for the authenticated user"""
    try:
        # Get all conversations for the user
        user_conversations = Conversation.objects.filter(participants=request.user)

        total_unread = 0
        for conversation in user_conversations:
            unread_count = conversation.messages.exclude(sender=request.user).exclude(
                read_statuses__user=request.user
            ).count()
            total_unread += unread_count

        return Response({
            'success': True,
            'count': total_unread
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_conversation(request, conversation_id):
    """Delete a conversation (remove user from participants)"""
    try:
        conversation = Conversation.objects.get(
            conversation_id=conversation_id,
            participants=request.user
        )

        # Remove user from conversation
        conversation.participants.remove(request.user)

        # If no participants left, delete the conversation
        if conversation.participants.count() == 0:
            conversation.delete()

        return Response({
            'success': True,
            'message': 'Conversation deleted'
        })
    except Conversation.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_users_for_chat(request):
    """Search for users to start a conversation with"""
    try:
        query = request.GET.get('q', '').strip()
        user_type = request.GET.get('type', '').strip()

        if not query:
            return Response({
                'success': False,
                'error': 'Search query is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Build search filter
        search_filter = Q(username__icontains=query) | Q(email__icontains=query)

        # Exclude current user
        users = CustomUser.objects.filter(search_filter).exclude(id=request.user.id)

        # Filter by user type if specified
        if user_type and user_type in ['Farmer', 'Buyer']:
            users = users.filter(user_type=user_type)

        # Limit results
        users = users[:10]

        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'first_name': user.first_name,
                'last_name': user.last_name
            })

        return Response({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Buyer Authentication Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_buyer(request):
    """Register a new buyer with email verification"""
    try:
        serializer = BuyerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Send welcome email with login credentials
            email_sent = send_buyer_welcome_email(
                user=user,
                password=user._generated_password,
                verification_token=user._verification_token,
                request=request
            )

            # Create notification
            if email_sent:
                Notification.objects.create(
                    user=user,
                    title="Welcome to Farm2Market!",
                    message="Welcome to Farm2Market! Please check your email to verify your account.",
                    notification_type="system_announcement"
                )
            else:
                Notification.objects.create(
                    user=user,
                    title="Welcome to Farm2Market!",
                    message="Welcome to Farm2Market! There was an issue sending your welcome email. Please contact support.",
                    notification_type="system_announcement"
                )

            return Response({
                'success': True,
                'message': 'Buyer account created successfully! Please check your email for login credentials.',
                'user_id': user.id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_buyer(request):
    """Login buyer and return authentication token"""
    try:
        serializer = BuyerLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Create or get token
            token, created = Token.objects.get_or_create(user=user)

            # Get buyer profile
            try:
                buyer_profile = BuyerProfile.objects.get(buyer=user)
                profile_data = BuyerProfileSerializer(buyer_profile).data
            except BuyerProfile.DoesNotExist:
                profile_data = None

            return Response({
                'success': True,
                'message': 'Login successful',
                'user_id': user.id,
                'user_type': user.user_type,
                'token': token.key,
                'email': user.email,
                'username': user.username,
                'full_name': user.get_full_name(),
                'profile': profile_data
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    """Verify buyer email address"""
    try:
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']

            # Get verification token
            verification_token = EmailVerificationToken.objects.get(
                token=token,
                is_used=False
            )

            # Mark user as verified
            user = verification_token.user
            user.is_active = True
            user.save()

            # Mark token as used
            verification_token.is_used = True
            verification_token.save()

            # Create notification
            Notification.objects.create(
                user=user,
                title="Email Verified!",
                message="Your email has been verified successfully! You can now access all features.",
                notification_type="system_announcement"
            )

            return Response({
                'success': True,
                'message': 'Email verified successfully!'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except EmailVerificationToken.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Invalid or expired verification token'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_password_reset(request):
    """Request password reset for buyer"""
    try:
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = CustomUser.objects.get(email=email, user_type='Buyer')

            # Generate reset token
            import secrets
            from datetime import timedelta

            token = secrets.token_urlsafe(32)
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(hours=1)
            )

            # Send reset email
            email_sent = send_password_reset_email(
                user=user,
                reset_token=token,
                request=request
            )

            return Response({
                'success': True,
                'message': 'Password reset instructions have been sent to your email.'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """Reset password using token"""
    try:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            reset_token = serializer.validated_data['reset_token']
            new_password = serializer.validated_data['new_password']

            # Update user password
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            # Mark token as used
            reset_token.is_used = True
            reset_token.save()

            # Create notification
            Notification.objects.create(
                user=user,
                title="Password Reset",
                message="Your password has been reset successfully.",
                notification_type="system_announcement"
            )

            return Response({
                'success': True,
                'message': 'Password reset successfully! You can now login with your new password.'
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def buyer_profile(request):
    """Get or update buyer profile"""
    if request.user.user_type != 'Buyer':
        return Response({
            'success': False,
            'message': 'Only buyers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        profile = BuyerProfile.objects.get(buyer=request.user)
    except BuyerProfile.DoesNotExist:
        profile = BuyerProfile.objects.create(buyer=request.user)

    if request.method == 'GET':
        # Return both user and profile data
        user_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone_number': request.user.phone_number
        }

        serializer = BuyerProfileSerializer(profile)
        return Response({
            'success': True,
            'user': user_data,
            'profile': serializer.data
        })

    elif request.method == 'PUT':
        # Update user fields if provided
        user_fields = ['first_name', 'last_name', 'phone_number']
        user_updated = False

        for field in user_fields:
            if field in request.data:
                setattr(request.user, field, request.data[field])
                user_updated = True

        if user_updated:
            request.user.save()

        # Update profile fields
        profile_data = {k: v for k, v in request.data.items() if k not in user_fields}

        serializer = BuyerProfileSerializer(profile, data=profile_data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Return updated data
            updated_user_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'phone_number': request.user.phone_number
            }

            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': updated_user_data,
                'profile': BuyerProfileSerializer(profile).data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def buyer_dashboard_data(request):
    """Get buyer dashboard statistics"""
    if request.user.user_type != 'Buyer':
        return Response({
            'success': False,
            'message': 'Only buyers can access dashboard data'
        }, status=status.HTTP_403_FORBIDDEN)

    # Get buyer's reservations
    reservations = Reservation.objects.filter(buyer=request.user)
    pending_reservations = reservations.filter(status='Pending').count()
    approved_reservations = reservations.filter(status='Approved').count()

    # Get recent transactions (this month)
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    transactions = Transaction.objects.filter(
        buyer=request.user,
        status='Successful',
        created_at__gte=current_month
    )

    total_spent = sum(
        reservation.listing.price * reservation.quantity
        for transaction in transactions
        for reservation in [transaction.reservation]
    )

    # Get unread notifications
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return Response({
        'success': True,
        'dashboard_data': {
            'pending_reservations': pending_reservations,
            'approved_reservations': approved_reservations,
            'monthly_spending': float(total_spent),
            'unread_notifications': unread_notifications,
            'total_reservations': reservations.count()
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def buyer_purchase_history(request):
    """Get buyer's purchase history with filtering and pagination"""
    if request.user.user_type != 'Buyer':
        return Response({
            'success': False,
            'message': 'Only buyers can access purchase history'
        }, status=status.HTTP_403_FORBIDDEN)

    try:
        # Get query parameters
        status_filter = request.GET.get('status', 'all')  # all, pending, approved, completed, rejected
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))

        # Base query for buyer's reservations
        reservations = Reservation.objects.filter(buyer=request.user).select_related(
            'listing', 'listing__farmer'
        ).order_by('-created_at')

        # Apply status filter
        if status_filter != 'all':
            reservations = reservations.filter(status__iexact=status_filter)

        # Apply date filters
        if date_from:
            try:
                from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
                reservations = reservations.filter(created_at__date__gte=from_date)
            except ValueError:
                pass

        if date_to:
            try:
                to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
                reservations = reservations.filter(created_at__date__lte=to_date)
            except ValueError:
                pass

        # Pagination
        total_count = reservations.count()
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_reservations = reservations[start_index:end_index]

        # Prepare response data
        purchase_history = []
        for reservation in paginated_reservations:
            # Get transaction if exists
            transaction = None
            try:
                transaction = Transaction.objects.get(reservation=reservation)
            except Transaction.DoesNotExist:
                pass

            purchase_data = {
                'reservation_id': reservation.reservation_id,
                'date': reservation.created_at.strftime('%Y-%m-%d'),
                'time': reservation.created_at.strftime('%H:%M'),
                'product_name': reservation.listing.product_name,
                'farmer_name': reservation.listing.farmer.get_full_name(),
                'farmer_username': reservation.listing.farmer.username,
                'quantity': reservation.quantity,
                'unit_price': float(reservation.unit_price),
                'total_amount': float(reservation.total_amount),
                'status': reservation.status,
                'delivery_method': reservation.delivery_method,
                'special_instructions': reservation.special_instructions,
                'product_image': reservation.listing.image_url,
                'category': reservation.listing.category.name if reservation.listing.category else None,
                'transaction_status': transaction.status if transaction else 'No Transaction',
                'payment_method': transaction.payment_method if transaction else None,
                'receipt_url': transaction.receipt_url if transaction else None,
            }
            purchase_history.append(purchase_data)

        # Calculate summary statistics
        all_reservations = Reservation.objects.filter(buyer=request.user)
        summary = {
            'total_purchases': all_reservations.count(),
            'pending_count': all_reservations.filter(status='Pending').count(),
            'approved_count': all_reservations.filter(status='Approved').count(),
            'completed_count': all_reservations.filter(status='Completed').count(),
            'rejected_count': all_reservations.filter(status='Rejected').count(),
            'total_spent': float(sum(r.total_amount for r in all_reservations if r.total_amount)),
        }

        return Response({
            'success': True,
            'purchase_history': purchase_history,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page,
                'has_next': end_index < total_count,
                'has_previous': page > 1
            },
            'summary': summary
        })

    except Exception as e:
        logger.error(f"Error getting buyer purchase history: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve purchase history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Buyer Marketplace Views
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_products(request):
    """Search for products and farmers"""
    try:
        query = request.GET.get('q', '').strip()
        search_type = request.GET.get('type', 'all')  # 'product', 'farmer', or 'all'

        results = {
            'products': [],
            'farmers': []
        }

        if query:
            # Search products by name
            if search_type in ['product', 'all']:
                product_listings = FarmerListing.objects.filter(
                    product_name__icontains=query,
                    status='Available'
                ).select_related('farmer').order_by('farmer__first_name', 'farmer__last_name')

                for listing in product_listings:
                    results['products'].append({
                        'listing_id': listing.listing_id,
                        'product_name': listing.product_name,
                        'description': listing.description,
                        'price': float(listing.price),
                        'quantity': listing.quantity,
                        'quantity_unit': listing.quantity_unit,
                        'image_url': listing.image_url,
                        'farmer_id': listing.farmer.id,
                        'farmer_name': f"{listing.farmer.first_name} {listing.farmer.last_name}".strip() or listing.farmer.username,
                        'farmer_location': getattr(listing.farmer.farmerprofile, 'location', '') if hasattr(listing.farmer, 'farmerprofile') else '',
                        'created_at': listing.created_at
                    })

            # Search farmers by name
            if search_type in ['farmer', 'all']:
                farmers = CustomUser.objects.filter(
                    user_type='Farmer',
                    is_approved=True
                ).filter(
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(username__icontains=query)
                ).order_by('first_name', 'last_name')

                for farmer in farmers:
                    # Get farmer's active listings count
                    active_listings = FarmerListing.objects.filter(
                        farmer=farmer,
                        status='Available'
                    ).count()

                    farmer_profile = getattr(farmer, 'farmerprofile', None)

                    results['farmers'].append({
                        'farmer_id': farmer.id,
                        'farmer_name': f"{farmer.first_name} {farmer.last_name}".strip() or farmer.username,
                        'username': farmer.username,
                        'location': farmer_profile.location if farmer_profile else '',
                        'trust_badge': farmer_profile.trust_badge if farmer_profile else False,
                        'active_listings_count': active_listings,
                        'email': farmer.email
                    })

        return Response({
            'success': True,
            'query': query,
            'results': results
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_all_products(request):
    """Get all available products from all farmers"""
    try:
        # Get all available listings ordered by farmer name
        listings = FarmerListing.objects.filter(
            status='Available'
        ).select_related('farmer').order_by('farmer__first_name', 'farmer__last_name', 'product_name')

        products = []
        for listing in listings:
            farmer_profile = getattr(listing.farmer, 'farmerprofile', None)

            products.append({
                'listing_id': listing.listing_id,
                'product_name': listing.product_name,
                'description': listing.description,
                'price': float(listing.price),
                'quantity': listing.quantity,
                'quantity_unit': listing.quantity_unit,
                'image_url': listing.image_url,
                'farmer_id': listing.farmer.id,
                'farmer_name': f"{listing.farmer.first_name} {listing.farmer.last_name}".strip() or listing.farmer.username,
                'farmer_location': farmer_profile.location if farmer_profile else '',
                'farmer_trust_badge': farmer_profile.trust_badge if farmer_profile else False,
                'created_at': listing.created_at
            })

        return Response({
            'success': True,
            'products': products,
            'total_count': len(products)
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_product_details(request, listing_id):
    """Get detailed information about a specific product listing"""
    try:
        listing = FarmerListing.objects.select_related('farmer').get(
            listing_id=listing_id,
            status='Available'
        )

        farmer_profile = getattr(listing.farmer, 'farmerprofile', None)

        # Get product categories
        categories = ProductCategory.objects.filter(listing=listing).select_related('category')
        category_names = [pc.category.name for pc in categories]

        # Get farmer's other products
        other_products = FarmerListing.objects.filter(
            farmer=listing.farmer,
            status='Available'
        ).exclude(listing_id=listing_id)[:5]

        other_products_data = []
        for product in other_products:
            other_products_data.append({
                'listing_id': product.listing_id,
                'product_name': product.product_name,
                'price': float(product.price),
                'quantity': product.quantity,
                'quantity_unit': product.quantity_unit,
                'image_url': product.image_url
            })

        product_details = {
            'listing_id': listing.listing_id,
            'product_name': listing.product_name,
            'description': listing.description,
            'price': float(listing.price),
            'quantity': listing.quantity,
            'quantity_unit': listing.quantity_unit,
            'image_url': listing.image_url,
            'categories': category_names,
            'created_at': listing.created_at,
            'farmer': {
                'farmer_id': listing.farmer.id,
                'name': f"{listing.farmer.first_name} {listing.farmer.last_name}".strip() or listing.farmer.username,
                'username': listing.farmer.username,
                'email': listing.farmer.email,
                'phone': listing.farmer.phone_number,
                'location': farmer_profile.location if farmer_profile else '',
                'trust_badge': farmer_profile.trust_badge if farmer_profile else False
            },
            'other_products': other_products_data
        }

        return Response({
            'success': True,
            'product': product_details
        })

    except FarmerListing.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Product not found or no longer available'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Enhanced Chat/Messaging Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_conversations(request):
    """Get all conversations for the authenticated user"""
    try:
        user = request.user
        conversations = Conversation.objects.filter(
            participants=user,
            is_active=True
        ).prefetch_related('participants', 'messages')

        conversation_data = []
        for conversation in conversations:
            other_participant = conversation.get_other_participant(user)
            last_message = conversation.get_last_message()
            unread_count = conversation.get_unread_count_for_user(user)

            conversation_data.append({
                'conversation_id': conversation.conversation_id,
                'conversation_type': conversation.conversation_type,
                'title': conversation.title or f"Chat with {other_participant.first_name}",
                'other_participant': {
                    'user_id': other_participant.id,
                    'name': f"{other_participant.first_name} {other_participant.last_name}",
                    'username': other_participant.username,
                    'user_type': other_participant.user_type,
                },
                'last_message': {
                    'content': last_message.content if last_message else None,
                    'created_at': last_message.created_at if last_message else None,
                    'sender_name': f"{last_message.sender.first_name}" if last_message else None,
                } if last_message else None,
                'unread_count': unread_count,
                'updated_at': conversation.updated_at,
                'related_listing': {
                    'listing_id': conversation.related_listing.listing_id,
                    'product_name': conversation.related_listing.product_name,
                } if conversation.related_listing else None,
            })

        return Response({
            'success': True,
            'conversations': conversation_data
        })

    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve conversations'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_conversation_messages(request, conversation_id):
    """Get all messages in a specific conversation"""
    try:
        user = request.user

        # Verify user is participant in conversation
        conversation = Conversation.objects.filter(
            conversation_id=conversation_id,
            participants=user
        ).first()

        if not conversation:
            return Response({
                'success': False,
                'error': 'Conversation not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get messages
        messages = Message.objects.filter(
            conversation=conversation
        ).select_related('sender').order_by('created_at')

        message_data = []
        for message in messages:
            # Check if user has read this message
            is_read = MessageReadStatus.objects.filter(
                message=message,
                user=user
            ).exists()

            message_data.append({
                'message_id': message.message_id,
                'content': message.content,
                'sender': {
                    'user_id': message.sender.id,
                    'name': f"{message.sender.first_name} {message.sender.last_name}",
                    'user_type': message.sender.user_type,
                },
                'is_own_message': message.sender == user,
                'is_read': is_read,
                'created_at': message.created_at,
            })

        # Mark all messages as read for this user
        conversation.mark_all_as_read_for_user(user)

        return Response({
            'success': True,
            'conversation': {
                'conversation_id': conversation.conversation_id,
                'title': conversation.title,
                'conversation_type': conversation.conversation_type,
            },
            'messages': message_data
        })

    except Exception as e:
        logger.error(f"Error getting conversation messages: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve messages'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_message(request):
    """Send a new message in a conversation"""
    try:
        user = request.user
        conversation_id = request.data.get('conversation_id')
        message_text = request.data.get('message_text', '').strip()

        if not conversation_id or not message_text:
            return Response({
                'success': False,
                'error': 'Conversation ID and message text are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify user is participant in conversation
        conversation = Conversation.objects.filter(
            conversation_id=conversation_id,
            participants=user
        ).first()

        if not conversation:
            return Response({
                'success': False,
                'error': 'Conversation not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=message_text
        )

        # Update conversation timestamp
        conversation.update_last_message_time()

        # Create notification for other participant
        other_participant = conversation.get_other_participant(user)
        if other_participant:
            Notification.objects.create(
                user=other_participant,
                title="New Message",
                message=f"You have a new message from {user.first_name}",
                notification_type="new_message",
                conversation=conversation
            )

        return Response({
            'success': True,
            'message': {
                'message_id': message.message_id,
                'content': message.content,
                'created_at': message.created_at,
                'sender': {
                    'user_id': user.id,
                    'name': f"{user.first_name} {user.last_name}",
                    'user_type': user.user_type,
                }
            }
        })

    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to send message'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_conversation(request):
    """Start a new conversation with another user"""
    try:
        user = request.user
        recipient_id = request.data.get('recipient_id')
        initial_message = request.data.get('initial_message', '').strip()
        conversation_type = request.data.get('conversation_type', 'direct')
        listing_id = request.data.get('listing_id')  # Optional

        if not recipient_id:
            return Response({
                'success': False,
                'error': 'Recipient ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get recipient
        try:
            recipient = CustomUser.objects.get(id=recipient_id)
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Recipient not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if conversation already exists
        existing_conversation = Conversation.objects.filter(
            participants=user
        ).filter(
            participants=recipient
        ).first()

        if existing_conversation:
            return Response({
                'success': True,
                'conversation_id': existing_conversation.conversation_id,
                'message': 'Conversation already exists'
            })

        # Create new conversation
        conversation = Conversation.objects.create(
            conversation_type=conversation_type,
            title=f"Chat between {user.first_name} and {recipient.first_name}"
        )

        # Add participants
        conversation.participants.add(user, recipient)

        # Add related listing if provided
        if listing_id:
            try:
                listing = FarmerListing.objects.get(listing_id=listing_id)
                conversation.related_listing = listing
                conversation.save()
            except FarmerListing.DoesNotExist:
                pass

        # Send initial message if provided
        if initial_message:
            Message.objects.create(
                conversation=conversation,
                sender=user,
                content=initial_message
            )
            conversation.update_last_message_time()

        return Response({
            'success': True,
            'conversation_id': conversation.conversation_id,
            'message': 'Conversation started successfully'
        })

    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to start conversation'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Receipt Upload System Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_receipt(request):
    """Upload payment receipt for a transaction"""
    try:
        user = request.user
        transaction_id = request.data.get('transaction_id')
        receipt_notes = request.data.get('receipt_notes', '')
        receipt_image = request.FILES.get('receipt_image')

        if not transaction_id:
            return Response({
                'success': False,
                'error': 'Transaction ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get transaction and verify ownership
        try:
            transaction = Transaction.objects.get(
                transaction_id=transaction_id,
                buyer=user
            )
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Transaction not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if transaction is in correct state
        if transaction.status not in ['pending_payment', 'receipt_rejected']:
            return Response({
                'success': False,
                'error': 'Receipt cannot be uploaded for this transaction'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update transaction with receipt
        if receipt_image:
            transaction.receipt_image = receipt_image
        transaction.receipt_notes = receipt_notes
        transaction.status = 'receipt_uploaded'
        transaction.save()

        # Create file upload record
        if receipt_image:
            FileUpload.objects.create(
                uploaded_by=user,
                file_name=receipt_image.name,
                file_type='receipt',
                file_path=transaction.receipt_image.url,
                file_size=receipt_image.size,
                mime_type=receipt_image.content_type,
                related_transaction=transaction
            )

        # Notify farmer
        Notification.objects.create(
            user=transaction.farmer,
            title="Receipt Uploaded",
            message=f"Payment receipt uploaded for {transaction.reservation.listing.product_name}",
            notification_type="receipt_uploaded",
            transaction=transaction
        )

        return Response({
            'success': True,
            'message': 'Receipt uploaded successfully',
            'transaction_status': transaction.status
        })

    except Exception as e:
        logger.error(f"Error uploading receipt: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to upload receipt'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_receipt(request, transaction_id):
    """Farmer verifies uploaded receipt"""
    try:
        user = request.user
        action = request.data.get('action')  # 'approve' or 'reject'
        notes = request.data.get('notes', '')

        if action not in ['approve', 'reject']:
            return Response({
                'success': False,
                'error': 'Action must be "approve" or "reject"'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get transaction and verify farmer ownership
        try:
            transaction = Transaction.objects.get(
                transaction_id=transaction_id,
                farmer=user
            )
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Transaction not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if transaction has uploaded receipt
        if transaction.status != 'receipt_uploaded':
            return Response({
                'success': False,
                'error': 'No receipt to verify for this transaction'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update transaction based on action
        if action == 'approve':
            transaction.verify_receipt(user, notes)
            notification_title = "Receipt Approved"
            notification_message = f"Your payment receipt has been approved for {transaction.reservation.listing.product_name}"
            notification_type = "receipt_verified"
        else:
            transaction.reject_receipt(user, notes)
            notification_title = "Receipt Rejected"
            notification_message = f"Your payment receipt was rejected for {transaction.reservation.listing.product_name}. Please upload a new receipt."
            notification_type = "receipt_rejected"

        # Notify buyer
        Notification.objects.create(
            user=transaction.buyer,
            title=notification_title,
            message=notification_message,
            notification_type=notification_type,
            transaction=transaction
        )

        return Response({
            'success': True,
            'message': f'Receipt {action}d successfully',
            'transaction_status': transaction.status
        })

    except Exception as e:
        logger.error(f"Error verifying receipt: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to verify receipt'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# General Authentication Views (for frontend compatibility)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def general_login(request):
    """General login endpoint that works for both farmers and buyers"""
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'success': False,
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate user
        user = authenticate(username=email, password=password)
        if not user:
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_approved:
            return Response({
                'success': False,
                'error': 'Account pending approval'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get or create token
        token, created = Token.objects.get_or_create(user=user)

        # Get user profile data
        profile_data = {}
        if user.user_type == 'Farmer':
            try:
                profile = FarmerProfile.objects.get(farmer=user)
                profile_data = {
                    'location': profile.location,
                    'trust_badge': profile.trust_badge,
                    'farm_description': profile.farm_description
                }
            except FarmerProfile.DoesNotExist:
                pass
        elif user.user_type == 'Buyer':
            try:
                profile = BuyerProfile.objects.get(buyer=user)
                profile_data = {
                    'location': profile.location,
                    'delivery_address': profile.delivery_address,
                    'preferred_delivery_method': profile.preferred_delivery_method
                }
            except BuyerProfile.DoesNotExist:
                pass

        return Response({
            'success': True,
            'message': 'Login successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'profile': profile_data
            }
        })

    except Exception as e:
        logger.error(f"Error in general login: {str(e)}")
        return Response({
            'success': False,
            'error': 'Login failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def general_register(request):
    """General registration endpoint"""
    try:
        user_type = request.data.get('user_type', 'Buyer')

        if user_type == 'Farmer':
            return register_farmer(request)
        else:
            return register_buyer(request)

    except Exception as e:
        logger.error(f"Error in general registration: {str(e)}")
        return Response({
            'success': False,
            'error': 'Registration failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Farmer Authentication Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_farmer(request):
    """Register a new farmer"""
    try:
        # Use the existing user registration logic but set user_type to Farmer
        data = request.data.copy()
        data['user_type'] = 'Farmer'

        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()

            # Create farmer profile
            FarmerProfile.objects.create(
                farmer=user,
                location=data.get('location', '')
            )

            # Send notification to admin
            admin_users = CustomUser.objects.filter(user_type='Admin', is_active=True)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title="New Farmer Registration",
                    message=f"New farmer registration: {user.username} ({user.email}) requires approval.",
                    notification_type="system_announcement"
                )

            # Send confirmation email to farmer
            send_farmer_registration_email(user)

            return Response({
                'success': True,
                'message': 'Registration submitted successfully. Your account is pending admin approval.',
                'user_id': user.id,
                'email': user.email,
                'requires_approval': True
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error in farmer registration: {str(e)}")
        return Response({
            'success': False,
            'error': 'Registration failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_farmer(request):
    """Login farmer and return authentication token"""
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'success': False,
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate user
        user = authenticate(username=email, password=password)
        if not user or user.user_type != 'Farmer':
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_approved:
            return Response({
                'success': False,
                'error': 'Account pending approval'
            }, status=status.HTTP_403_FORBIDDEN)

        # Create or get token
        token, created = Token.objects.get_or_create(user=user)

        # Get farmer profile
        try:
            farmer_profile = FarmerProfile.objects.get(farmer=user)
            profile_data = FarmerProfileSerializer(farmer_profile).data
        except FarmerProfile.DoesNotExist:
            profile_data = None

        return Response({
            'success': True,
            'message': 'Login successful',
            'user_id': user.id,
            'user_type': user.user_type,
            'token': token.key,
            'email': user.email,
            'username': user.username,
            'full_name': user.get_full_name(),
            'profile': profile_data
        })

    except Exception as e:
        logger.error(f"Error in farmer login: {str(e)}")
        return Response({
            'success': False,
            'error': 'Login failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Enhanced Notification Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_notifications(request):
    """Get user's notifications with enhanced data"""
    try:
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

        # Count unread notifications
        unread_count = notifications.filter(is_read=False).count()

        notification_data = []
        for notification in notifications:
            notification_data.append({
                'notification_id': notification.notification_id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at,
                'read_at': notification.read_at,
                'data': notification.data
            })

        return Response({
            'success': True,
            'notifications': notification_data,
            'unread_count': unread_count
        })

    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to retrieve notifications'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(
            notification_id=notification_id,
            user=request.user
        )

        notification.mark_as_read()

        return Response({
            'success': True,
            'message': 'Notification marked as read'
        })

    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to mark notification as read'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_unread_messages_count(request):
    """Get count of unread messages for the authenticated user"""
    try:
        # Get all conversations for the user
        user_conversations = Conversation.objects.filter(participants=request.user)

        total_unread = 0
        for conversation in user_conversations:
            unread_count = conversation.get_unread_count_for_user(request.user)
            total_unread += unread_count

        return Response({
            'success': True,
            'unread_count': total_unread
        })

    except Exception as e:
        logger.error(f"Error getting unread messages count: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get unread messages count'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# COMPREHENSIVE ADMIN SYSTEM APIS
# ========================================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def admin_login(request):
    """Admin login endpoint"""
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'success': False,
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate user
        user = authenticate(username=email, password=password)
        if not user or user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Invalid admin credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({
                'success': False,
                'error': 'Admin account is deactivated'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get or create token
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'success': True,
            'message': 'Admin login successful',
            'token': token.key,
            'admin': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined
            }
        })

    except Exception as e:
        logger.error(f"Error in admin login: {str(e)}")
        return Response({
            'success': False,
            'error': 'Login failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_admin(request):
    """Create a new admin user (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Only admins can create other admins'
            }, status=status.HTTP_403_FORBIDDEN)

        # Extract data
        username = request.data.get('username')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        password = request.data.get('password')
        is_superuser = request.data.get('is_superuser', False)

        # Validate required fields
        if not all([username, email, first_name, last_name, password]):
            return Response({
                'success': False,
                'error': 'All fields are required: username, email, first_name, last_name, password'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'error': 'Admin with this email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(username=username).exists():
            return Response({
                'success': False,
                'error': 'Admin with this username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check for password duplication across all users
        all_users = CustomUser.objects.all()
        for user in all_users:
            if user.check_password(password):
                return Response({
                    'success': False,
                    'error': 'This password is already in use by another user. Please choose a different password.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Create admin user
        admin_user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type='Admin',
            is_approved=True,
            is_active=True,
            is_staff=True,
            is_superuser=is_superuser
        )

        # Send welcome email to new admin
        try:
            send_admin_welcome_email(admin_user, password, request.user)
            email_sent = True
        except Exception as e:
            logger.error(f"Failed to send welcome email to admin {admin_user.email}: {str(e)}")
            email_sent = False

        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action_type='admin_action',
            description=f'Created new admin: {admin_user.username} ({admin_user.email})',
            related_object_type='CustomUser',
            related_object_id=admin_user.id
        )

        # Send notification to new admin
        Notification.objects.create(
            user=admin_user,
            title="Admin Account Created",
            message=f"Your admin account has been created by {request.user.username}. Welcome to Agriport! Check your email for login credentials.",
            notification_type="system_announcement"
        )

        return Response({
            'success': True,
            'message': f'Admin created successfully. {"Welcome email sent." if email_sent else "Email notification failed - please inform admin manually."}',
            'admin': {
                'id': admin_user.id,
                'username': admin_user.username,
                'email': admin_user.email,
                'first_name': admin_user.first_name,
                'last_name': admin_user.last_name,
                'is_superuser': admin_user.is_superuser,
                'date_joined': admin_user.date_joined
            },
            'email_sent': email_sent
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error creating admin: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to create admin'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_dashboard(request):
    """Get comprehensive admin dashboard data"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        # System statistics
        total_users = CustomUser.objects.count()
        total_farmers = CustomUser.objects.filter(user_type='Farmer').count()
        total_buyers = CustomUser.objects.filter(user_type='Buyer').count()
        total_admins = CustomUser.objects.filter(user_type='Admin').count()

        # Pending approvals
        pending_farmers = CustomUser.objects.filter(
            user_type='Farmer',
            is_approved=False,
            is_active=True
        ).count()

        # Active listings
        active_listings = FarmerListing.objects.filter(status='Available').count()

        # Recent transactions
        from datetime import datetime, timedelta
        last_30_days = timezone.now() - timedelta(days=30)
        recent_transactions = Transaction.objects.filter(
            created_at__gte=last_30_days
        ).count()

        # System revenue (last 30 days)
        successful_transactions = Transaction.objects.filter(
            status='Successful',
            created_at__gte=last_30_days
        )

        total_revenue = sum(
            transaction.reservation.listing.price * transaction.reservation.quantity
            for transaction in successful_transactions
        )

        # Recent activity
        recent_users = CustomUser.objects.filter(
            date_joined__gte=last_30_days
        ).order_by('-date_joined')[:10]

        recent_users_data = []
        for user in recent_users:
            recent_users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'date_joined': user.date_joined,
                'is_approved': user.is_approved
            })

        return Response({
            'success': True,
            'dashboard_data': {
                'system_stats': {
                    'total_users': total_users,
                    'total_farmers': total_farmers,
                    'total_buyers': total_buyers,
                    'total_admins': total_admins,
                    'pending_farmers': pending_farmers,
                    'active_listings': active_listings,
                    'recent_transactions': recent_transactions,
                    'total_revenue_30_days': float(total_revenue)
                },
                'recent_users': recent_users_data
            }
        })

    except Exception as e:
        logger.error(f"Error getting admin dashboard: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get dashboard data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_manage_users(request):
    """Get all users for admin management"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        user_type = request.GET.get('user_type', '')
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')

        # Base query
        users = CustomUser.objects.all().order_by('-date_joined')

        # Filter by user type
        if user_type and user_type in ['Farmer', 'Buyer', 'Admin']:
            users = users.filter(user_type=user_type)

        # Search filter
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        # Status filter
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        elif status_filter == 'pending':
            users = users.filter(is_approved=False, user_type='Farmer')

        # Paginate results
        from django.core.paginator import Paginator
        paginator = Paginator(users, 20)  # 20 users per page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        users_data = []
        for user in page_obj:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'is_active': user.is_active,
                'is_approved': user.is_approved,
                'date_joined': user.date_joined,
                'last_login': user.last_login
            }

            # Add profile data if available
            if user.user_type == 'Farmer':
                try:
                    profile = user.farmerprofile
                    user_data['profile'] = {
                        'location': profile.location,
                        'trust_badge': profile.trust_badge,
                        'farm_description': profile.farm_description
                    }
                except:
                    user_data['profile'] = None
            elif user.user_type == 'Buyer':
                try:
                    profile = user.buyerprofile
                    user_data['profile'] = {
                        'location': profile.location,
                        'delivery_address': profile.delivery_address,
                        'preferred_delivery_method': profile.preferred_delivery_method
                    }
                except:
                    user_data['profile'] = None

            users_data.append(user_data)

        return Response({
            'success': True,
            'users': users_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_users': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })

    except Exception as e:
        logger.error(f"Error managing users: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get users'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_view_details(request, admin_id):
    """View detailed admin information (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get admin details
        try:
            admin_user = CustomUser.objects.get(id=admin_id, user_type='Admin')
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get admin's recent activities
        recent_logs = AuditLog.objects.filter(user=admin_user).order_by('-created_at')[:10]

        admin_data = {
            'id': admin_user.id,
            'username': admin_user.username,
            'email': admin_user.email,
            'first_name': admin_user.first_name,
            'last_name': admin_user.last_name,
            'is_superuser': admin_user.is_superuser,
            'is_active': admin_user.is_active,
            'date_joined': admin_user.date_joined,
            'last_login': admin_user.last_login,
            'recent_activities': [
                {
                    'action': log.action_type,
                    'description': log.description,
                    'timestamp': log.created_at
                } for log in recent_logs
            ]
        }

        return Response({
            'success': True,
            'admin': admin_data
        })

    except Exception as e:
        logger.error(f"Error viewing admin details: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get admin details'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def admin_update(request, admin_id):
    """Update admin information (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get admin to update
        try:
            admin_user = CustomUser.objects.get(id=admin_id, user_type='Admin')
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Prevent non-superusers from editing superusers
        if admin_user.is_superuser and not request.user.is_superuser:
            return Response({
                'success': False,
                'error': 'Only superusers can edit other superusers'
            }, status=status.HTTP_403_FORBIDDEN)

        # Update allowed fields
        updatable_fields = ['first_name', 'last_name', 'email', 'is_active']
        if request.user.is_superuser:
            updatable_fields.append('is_superuser')

        updated_fields = []
        for field in updatable_fields:
            if field in request.data:
                old_value = getattr(admin_user, field)
                new_value = request.data[field]

                # Check for email uniqueness
                if field == 'email' and new_value != old_value:
                    if CustomUser.objects.filter(email=new_value).exclude(id=admin_id).exists():
                        return Response({
                            'success': False,
                            'error': 'Email already exists'
                        }, status=status.HTTP_400_BAD_REQUEST)

                setattr(admin_user, field, new_value)
                updated_fields.append(f"{field}: {old_value} → {new_value}")

        admin_user.save()

        # Log the update
        AuditLog.objects.create(
            user=request.user,
            action_type='admin_action',
            description=f'Updated admin {admin_user.username}: {", ".join(updated_fields)}',
            related_object_type='CustomUser',
            related_object_id=admin_user.id
        )

        return Response({
            'success': True,
            'message': 'Admin updated successfully',
            'updated_fields': updated_fields,
            'admin': {
                'id': admin_user.id,
                'username': admin_user.username,
                'email': admin_user.email,
                'first_name': admin_user.first_name,
                'last_name': admin_user.last_name,
                'is_superuser': admin_user.is_superuser,
                'is_active': admin_user.is_active
            }
        })

    except Exception as e:
        logger.error(f"Error updating admin: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update admin'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def admin_delete(request, admin_id):
    """Delete admin account (Superuser only)"""
    try:
        if not request.user.is_superuser:
            return Response({
                'success': False,
                'error': 'Superuser access required to delete admins'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get admin to delete
        try:
            admin_user = CustomUser.objects.get(id=admin_id, user_type='Admin')
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Admin not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Prevent self-deletion
        if admin_user.id == request.user.id:
            return Response({
                'success': False,
                'error': 'Cannot delete your own admin account'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Store admin info for logging
        admin_info = f"{admin_user.username} ({admin_user.email})"

        # Soft delete - deactivate instead of hard delete
        admin_user.is_active = False
        admin_user.save()

        # Log the deletion
        AuditLog.objects.create(
            user=request.user,
            action_type='admin_action',
            description=f'Deactivated admin account: {admin_info}',
            related_object_type='CustomUser',
            related_object_id=admin_user.id
        )

        return Response({
            'success': True,
            'message': f'Admin account {admin_info} has been deactivated'
        })

    except Exception as e:
        logger.error(f"Error deleting admin: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to delete admin'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# COMPREHENSIVE TRANSACTION MANAGEMENT
# ========================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_transactions(request):
    """Get all transactions with advanced filtering and sorting (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get query parameters
        status_filter = request.GET.get('status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        farmer_id = request.GET.get('farmer_id', '')
        buyer_id = request.GET.get('buyer_id', '')
        min_amount = request.GET.get('min_amount', '')
        max_amount = request.GET.get('max_amount', '')
        sort_by = request.GET.get('sort_by', '-created_at')
        search = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))

        # Base query
        transactions = Transaction.objects.all()

        # Apply filters
        if status_filter:
            transactions = transactions.filter(status=status_filter)

        if date_from:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            transactions = transactions.filter(created_at__gte=date_from_obj)

        if date_to:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            transactions = transactions.filter(created_at__lte=date_to_obj)

        if farmer_id:
            transactions = transactions.filter(reservation__listing__farmer_id=farmer_id)

        if buyer_id:
            transactions = transactions.filter(reservation__buyer_id=buyer_id)

        if min_amount:
            transactions = transactions.filter(amount__gte=float(min_amount))

        if max_amount:
            transactions = transactions.filter(amount__lte=float(max_amount))

        if search:
            transactions = transactions.filter(
                Q(reservation__listing__product_name__icontains=search) |
                Q(reservation__buyer__username__icontains=search) |
                Q(reservation__listing__farmer__username__icontains=search) |
                Q(transaction_id__icontains=search)
            )

        # Apply sorting
        valid_sort_fields = [
            'created_at', '-created_at', 'amount', '-amount',
            'status', '-status', 'updated_at', '-updated_at'
        ]
        if sort_by in valid_sort_fields:
            transactions = transactions.order_by(sort_by)
        else:
            transactions = transactions.order_by('-created_at')

        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(transactions, per_page)
        try:
            page_obj = paginator.get_page(page)
        except Exception as e:
            logger.error(f"Pagination error: {str(e)}")
            page_obj = paginator.get_page(1)

        # Serialize transaction data
        transaction_data = []
        for transaction in page_obj:
            try:
                reservation = transaction.reservation
                listing = reservation.listing
                farmer = listing.farmer
                buyer = reservation.buyer

                transaction_data.append({
                    'transaction_id': transaction.transaction_id,
                    'amount': float(transaction.amount),
                    'status': transaction.status,
                    'created_at': transaction.created_at,
                    'updated_at': transaction.updated_at,
                    'farmer': {
                        'id': farmer.id,
                        'username': farmer.username,
                        'email': farmer.email,
                        'full_name': f"{farmer.first_name} {farmer.last_name}"
                    },
                    'buyer': {
                        'id': buyer.id,
                        'username': buyer.username,
                        'email': buyer.email,
                        'full_name': f"{buyer.first_name} {buyer.last_name}"
                    },
                    'product': {
                        'name': listing.product_name,
                        'category': listing.category.name if listing.category else 'N/A',
                        'quantity': reservation.quantity,
                        'unit_price': float(listing.price)
                    },
                    'reservation': {
                        'id': reservation.id,
                        'status': reservation.status,
                        'created_at': reservation.created_at
                    }
                })
            except Exception as e:
                logger.error(f"Error serializing transaction {transaction.transaction_id}: {str(e)}")
                continue

        # Calculate statistics
        total_transactions = paginator.count
        try:
            total_amount = sum(float(t.amount) for t in transactions)
        except Exception as e:
            logger.error(f"Error calculating total amount: {str(e)}")
            total_amount = 0.0

        status_counts = {}
        try:
            for status_choice in Transaction.STATUS_CHOICES:
                status_key = status_choice[0]
                count = transactions.filter(status=status_key).count()
                status_counts[status_key] = count
        except Exception as e:
            logger.error(f"Error calculating status counts: {str(e)}")
            status_counts = {}

        return Response({
            'success': True,
            'transactions': transaction_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_transactions': total_transactions,
                'per_page': per_page,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'statistics': {
                'total_amount': total_amount,
                'status_counts': status_counts
            },
            'filters_applied': {
                'status': status_filter,
                'date_from': date_from,
                'date_to': date_to,
                'farmer_id': farmer_id,
                'buyer_id': buyer_id,
                'min_amount': min_amount,
                'max_amount': max_amount,
                'search': search,
                'sort_by': sort_by
            }
        })

    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get transactions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_transaction_details(request, transaction_id):
    """Get detailed transaction information (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)

        reservation = transaction.reservation
        listing = reservation.listing
        farmer = listing.farmer
        buyer = reservation.buyer

        # Get farmer profile
        try:
            farmer_profile = farmer.farmerprofile
            farmer_profile_data = {
                'location': farmer_profile.location,
                'trust_badge': farmer_profile.trust_badge,
                'farm_description': farmer_profile.farm_description
            }
        except:
            farmer_profile_data = None

        # Get buyer profile
        try:
            buyer_profile = buyer.buyerprofile
            buyer_profile_data = {
                'location': buyer_profile.location,
                'delivery_address': buyer_profile.delivery_address,
                'preferred_delivery_method': buyer_profile.preferred_delivery_method
            }
        except:
            buyer_profile_data = None

        transaction_details = {
            'transaction_id': transaction.transaction_id,
            'amount': float(transaction.amount),
            'status': transaction.status,
            'created_at': transaction.created_at,
            'updated_at': transaction.updated_at,
            'farmer': {
                'id': farmer.id,
                'username': farmer.username,
                'email': farmer.email,
                'first_name': farmer.first_name,
                'last_name': farmer.last_name,
                'phone_number': farmer.phone_number,
                'date_joined': farmer.date_joined,
                'profile': farmer_profile_data
            },
            'buyer': {
                'id': buyer.id,
                'username': buyer.username,
                'email': buyer.email,
                'first_name': buyer.first_name,
                'last_name': buyer.last_name,
                'phone_number': buyer.phone_number,
                'date_joined': buyer.date_joined,
                'profile': buyer_profile_data
            },
            'product': {
                'name': listing.product_name,
                'description': listing.description,
                'category': listing.category.name if listing.category else 'N/A',
                'quantity_available': listing.quantity_available,
                'unit_price': float(listing.price),
                'location': listing.location,
                'harvest_date': listing.harvest_date,
                'status': listing.status
            },
            'reservation': {
                'id': reservation.id,
                'quantity': reservation.quantity,
                'total_price': float(reservation.quantity * listing.price),
                'status': reservation.status,
                'created_at': reservation.created_at,
                'updated_at': reservation.updated_at,
                'notes': reservation.notes
            }
        }

        return Response({
            'success': True,
            'transaction': transaction_details
        })

    except Exception as e:
        logger.error(f"Error getting transaction details: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get transaction details'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def admin_update_transaction(request, transaction_id):
    """Update transaction status (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
        except Transaction.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        admin_notes = request.data.get('admin_notes', '')

        if not new_status:
            return Response({
                'success': False,
                'error': 'Status is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate status
        valid_statuses = [choice[0] for choice in Transaction.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({
                'success': False,
                'error': f'Invalid status. Valid options: {", ".join(valid_statuses)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        old_status = transaction.status
        transaction.status = new_status
        transaction.save()

        # Log the update
        AuditLog.objects.create(
            user=request.user,
            action_type='transaction_update',
            description=f'Updated transaction {transaction_id} status from {old_status} to {new_status}. Notes: {admin_notes}',
            related_object_type='Transaction',
            related_object_id=transaction.id
        )

        # Send notifications to farmer and buyer
        farmer = transaction.reservation.listing.farmer
        buyer = transaction.reservation.buyer

        notification_message = f"Transaction {transaction_id} status updated to {new_status} by admin."
        if admin_notes:
            notification_message += f" Notes: {admin_notes}"

        for user in [farmer, buyer]:
            Notification.objects.create(
                user=user,
                title="Transaction Status Updated",
                message=notification_message,
                notification_type="transaction_update"
            )

        return Response({
            'success': True,
            'message': f'Transaction status updated from {old_status} to {new_status}',
            'transaction': {
                'transaction_id': transaction.transaction_id,
                'old_status': old_status,
                'new_status': new_status,
                'updated_at': transaction.updated_at
            }
        })

    except Exception as e:
        logger.error(f"Error updating transaction: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update transaction'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# ADVANCED USER MANAGEMENT SYSTEM
# ========================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_user_details(request, user_id):
    """Get detailed user information with profile and activity (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Base user data
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'user_type': user.user_type,
            'is_active': user.is_active,
            'is_approved': user.is_approved,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'profile': None,
            'statistics': {},
            'recent_activity': []
        }

        # Get profile data based on user type
        if user.user_type == 'Farmer':
            try:
                profile = user.farmerprofile
                user_data['profile'] = {
                    'location': profile.location,
                    'trust_badge': profile.trust_badge,
                    'farm_description': profile.farm_description
                }

                # Farmer statistics
                listings = FarmerListing.objects.filter(farmer=user)
                reservations = Reservation.objects.filter(listing__farmer=user)
                transactions = Transaction.objects.filter(reservation__listing__farmer=user)

                user_data['statistics'] = {
                    'total_listings': listings.count(),
                    'active_listings': listings.filter(status='Available').count(),
                    'total_reservations': reservations.count(),
                    'approved_reservations': reservations.filter(status='Approved').count(),
                    'total_transactions': transactions.count(),
                    'successful_transactions': transactions.filter(status='Successful').count(),
                    'total_revenue': sum(float(t.amount) for t in transactions.filter(status='Successful'))
                }

                # Recent farmer activity
                recent_listings = listings.order_by('-created_at')[:5]
                for listing in recent_listings:
                    user_data['recent_activity'].append({
                        'type': 'listing_created',
                        'description': f'Created listing: {listing.product_name}',
                        'timestamp': listing.created_at
                    })

            except Exception as e:
                logger.error(f"Error getting farmer profile: {str(e)}")

        elif user.user_type == 'Buyer':
            try:
                profile = user.buyerprofile
                user_data['profile'] = {
                    'location': profile.location,
                    'delivery_address': profile.delivery_address,
                    'preferred_delivery_method': profile.preferred_delivery_method
                }

                # Buyer statistics
                reservations = Reservation.objects.filter(buyer=user)
                transactions = Transaction.objects.filter(reservation__buyer=user)

                user_data['statistics'] = {
                    'total_reservations': reservations.count(),
                    'approved_reservations': reservations.filter(status='Approved').count(),
                    'pending_reservations': reservations.filter(status='Pending').count(),
                    'total_transactions': transactions.count(),
                    'successful_transactions': transactions.filter(status='Successful').count(),
                    'total_spent': sum(float(t.amount) for t in transactions.filter(status='Successful'))
                }

                # Recent buyer activity
                recent_reservations = reservations.order_by('-created_at')[:5]
                for reservation in recent_reservations:
                    user_data['recent_activity'].append({
                        'type': 'reservation_made',
                        'description': f'Made reservation for {reservation.listing.product_name}',
                        'timestamp': reservation.created_at
                    })

            except Exception as e:
                logger.error(f"Error getting buyer profile: {str(e)}")

        # Get recent notifications
        recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
        user_data['recent_notifications'] = [
            {
                'title': notif.title,
                'message': notif.message,
                'is_read': notif.is_read,
                'created_at': notif.created_at
            } for notif in recent_notifications
        ]

        return Response({
            'success': True,
            'user': user_data
        })

    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get user details'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def admin_update_user(request, user_id):
    """Update user information and profile (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Prevent editing admin users unless superuser
        if user.user_type == 'Admin' and not request.user.is_superuser:
            return Response({
                'success': False,
                'error': 'Only superusers can edit admin accounts'
            }, status=status.HTTP_403_FORBIDDEN)

        # Update user fields
        user_fields = ['first_name', 'last_name', 'email', 'phone_number', 'is_active']
        if request.user.is_superuser:
            user_fields.append('is_approved')

        updated_fields = []
        for field in user_fields:
            if field in request.data:
                old_value = getattr(user, field)
                new_value = request.data[field]

                # Check email uniqueness
                if field == 'email' and new_value != old_value:
                    if CustomUser.objects.filter(email=new_value).exclude(id=user_id).exists():
                        return Response({
                            'success': False,
                            'error': 'Email already exists'
                        }, status=status.HTTP_400_BAD_REQUEST)

                setattr(user, field, new_value)
                updated_fields.append(f"{field}: {old_value} → {new_value}")

        user.save()

        # Update profile if provided - WITH REAL SYSTEM IMPACT
        profile_updated = []
        system_impact = []

        if user.user_type == 'Farmer' and 'profile' in request.data:
            try:
                profile = user.farmerprofile
                profile_data = request.data['profile']

                profile_fields = ['location', 'farm_description', 'trust_badge']
                for field in profile_fields:
                    if field in profile_data:
                        old_value = getattr(profile, field)
                        new_value = profile_data[field]
                        setattr(profile, field, new_value)
                        profile_updated.append(f"profile.{field}: {old_value} → {new_value}")

                        # REAL SYSTEM IMPACT: Update related data
                        if field == 'location':
                            # Update all farmer's listings with new location
                            listings_updated = FarmerListing.objects.filter(farmer=user).update(location=new_value)
                            system_impact.append(f"Updated {listings_updated} listings with new location")

                        elif field == 'trust_badge':
                            # If trust badge changed, notify all buyers who have reservations with this farmer
                            reservations = Reservation.objects.filter(listing__farmer=user, status='Approved')
                            for reservation in reservations:
                                Notification.objects.create(
                                    user=reservation.buyer,
                                    title="Farmer Profile Updated",
                                    message=f"Farmer {user.username} has updated their trust badge status.",
                                    notification_type="farmer_update"
                                )
                            system_impact.append(f"Notified {reservations.count()} buyers about trust badge change")

                profile.save()
            except Exception as e:
                logger.error(f"Error updating farmer profile: {str(e)}")

        elif user.user_type == 'Buyer' and 'profile' in request.data:
            try:
                profile = user.buyerprofile
                profile_data = request.data['profile']

                profile_fields = ['location', 'delivery_address', 'preferred_delivery_method']
                for field in profile_fields:
                    if field in profile_data:
                        old_value = getattr(profile, field)
                        new_value = profile_data[field]
                        setattr(profile, field, new_value)
                        profile_updated.append(f"profile.{field}: {old_value} → {new_value}")

                        # REAL SYSTEM IMPACT: Update related data
                        if field == 'delivery_address':
                            # Update all pending reservations with new delivery address
                            pending_reservations = Reservation.objects.filter(buyer=user, status='Pending')
                            for reservation in pending_reservations:
                                reservation.notes = f"Updated delivery address: {new_value}"
                                reservation.save()

                                # Notify farmers about address change
                                Notification.objects.create(
                                    user=reservation.listing.farmer,
                                    title="Buyer Address Updated",
                                    message=f"Buyer {user.username} has updated their delivery address for reservation #{reservation.id}",
                                    notification_type="buyer_update"
                                )
                            system_impact.append(f"Updated {pending_reservations.count()} pending reservations with new address")

                profile.save()
            except Exception as e:
                logger.error(f"Error updating buyer profile: {str(e)}")

        # Handle account status changes with REAL IMPACT
        if 'is_active' in request.data:
            new_active_status = request.data['is_active']
            if not new_active_status and user.is_active:
                # User being deactivated - REAL SYSTEM IMPACT
                if user.user_type == 'Farmer':
                    # Deactivate all farmer's listings
                    listings = FarmerListing.objects.filter(farmer=user, status='Available')
                    listings_count = listings.update(status='Inactive')
                    system_impact.append(f"Deactivated {listings_count} farmer listings")

                    # Cancel all pending reservations
                    pending_reservations = Reservation.objects.filter(listing__farmer=user, status='Pending')
                    for reservation in pending_reservations:
                        reservation.status = 'Cancelled'
                        reservation.save()

                        # Notify buyers
                        Notification.objects.create(
                            user=reservation.buyer,
                            title="Reservation Cancelled",
                            message=f"Your reservation for {reservation.listing.product_name} has been cancelled due to farmer account deactivation.",
                            notification_type="reservation_cancelled"
                        )
                    system_impact.append(f"Cancelled {pending_reservations.count()} pending reservations")

                elif user.user_type == 'Buyer':
                    # Cancel all buyer's pending reservations
                    pending_reservations = Reservation.objects.filter(buyer=user, status='Pending')
                    for reservation in pending_reservations:
                        reservation.status = 'Cancelled'
                        reservation.save()

                        # Notify farmers
                        Notification.objects.create(
                            user=reservation.listing.farmer,
                            title="Reservation Cancelled",
                            message=f"Reservation from buyer {user.username} has been cancelled due to account deactivation.",
                            notification_type="reservation_cancelled"
                        )
                    system_impact.append(f"Cancelled {pending_reservations.count()} pending reservations")

            elif new_active_status and not user.is_active:
                # User being reactivated
                if user.user_type == 'Farmer':
                    # Reactivate farmer's listings (if they want)
                    inactive_listings = FarmerListing.objects.filter(farmer=user, status='Inactive')
                    system_impact.append(f"Found {inactive_listings.count()} inactive listings that can be reactivated")

                system_impact.append("Account reactivated - user can resume normal activities")

        # Log the update
        all_updates = updated_fields + profile_updated
        AuditLog.objects.create(
            user=request.user,
            action_type='user_update',
            description=f'Updated {user.user_type.lower()} {user.username}: {", ".join(all_updates)}',
            related_object_type='CustomUser',
            related_object_id=user.id
        )

        # Send notification to user
        if updated_fields or profile_updated:
            Notification.objects.create(
                user=user,
                title="Profile Updated",
                message=f"Your profile has been updated by an administrator. Changes: {', '.join(all_updates)}",
                notification_type="profile_update"
            )

        return Response({
            'success': True,
            'message': f'User {user.username} updated successfully with REAL system impact',
            'updated_fields': updated_fields,
            'profile_updated': profile_updated,
            'system_impact': system_impact,
            'total_changes': len(updated_fields) + len(profile_updated) + len(system_impact)
        })

    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update user'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def admin_delete_user(request, user_id):
    """Delete user account with REAL cascading effects (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Prevent deleting admin users unless superuser
        if user.user_type == 'Admin' and not request.user.is_superuser:
            return Response({
                'success': False,
                'error': 'Only superusers can delete admin accounts'
            }, status=status.HTTP_403_FORBIDDEN)

        # Prevent self-deletion
        if user.id == request.user.id:
            return Response({
                'success': False,
                'error': 'Cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Store user info for logging
        user_info = f"{user.username} ({user.email}) - {user.user_type}"

        # REAL CASCADING DELETION - Delete all related data
        deletion_summary = {
            'user_info': user_info,
            'deleted_data': {}
        }

        if user.user_type == 'Farmer':
            # Delete farmer-specific data
            try:
                farmer_profile = user.farmerprofile
                deletion_summary['deleted_data']['farmer_profile'] = True
            except:
                deletion_summary['deleted_data']['farmer_profile'] = False

            # Delete all farmer listings
            listings = FarmerListing.objects.filter(farmer=user)
            listings_count = listings.count()

            # Delete reservations for these listings
            reservations_count = 0
            transactions_count = 0
            for listing in listings:
                reservations = Reservation.objects.filter(listing=listing)
                for reservation in reservations:
                    # Delete transactions for these reservations
                    transactions = Transaction.objects.filter(reservation=reservation)
                    transactions_count += transactions.count()
                    transactions.delete()
                reservations_count += reservations.count()
                reservations.delete()

            # Delete the listings
            listings.delete()

            deletion_summary['deleted_data'].update({
                'listings': listings_count,
                'reservations': reservations_count,
                'transactions': transactions_count
            })

        elif user.user_type == 'Buyer':
            # Delete buyer-specific data
            try:
                buyer_profile = user.buyerprofile
                deletion_summary['deleted_data']['buyer_profile'] = True
            except:
                deletion_summary['deleted_data']['buyer_profile'] = False

            # Delete all buyer reservations
            reservations = Reservation.objects.filter(buyer=user)
            reservations_count = reservations.count()

            # Delete transactions for these reservations
            transactions_count = 0
            for reservation in reservations:
                transactions = Transaction.objects.filter(reservation=reservation)
                transactions_count += transactions.count()
                transactions.delete()

            # Delete the reservations
            reservations.delete()

            deletion_summary['deleted_data'].update({
                'reservations': reservations_count,
                'transactions': transactions_count
            })

        # Delete user's notifications
        notifications = Notification.objects.filter(user=user)
        notifications_count = notifications.count()
        notifications.delete()
        deletion_summary['deleted_data']['notifications'] = notifications_count

        # Delete user's conversations and messages
        conversations = Conversation.objects.filter(Q(farmer=user) | Q(buyer=user))
        conversations_count = conversations.count()
        messages_count = 0
        for conversation in conversations:
            messages = Message.objects.filter(conversation=conversation)
            messages_count += messages.count()
            messages.delete()
        conversations.delete()
        deletion_summary['deleted_data']['conversations'] = conversations_count
        deletion_summary['deleted_data']['messages'] = messages_count

        # Delete user's tokens
        try:
            Token.objects.filter(user=user).delete()
            deletion_summary['deleted_data']['auth_tokens'] = True
        except:
            deletion_summary['deleted_data']['auth_tokens'] = False

        # Delete role assignments if admin
        if user.user_type == 'Admin':
            try:
                from .models import AdminRoleAssignment
                role_assignments = AdminRoleAssignment.objects.filter(admin_user=user)
                role_assignments_count = role_assignments.count()
                role_assignments.delete()
                deletion_summary['deleted_data']['role_assignments'] = role_assignments_count
            except:
                deletion_summary['deleted_data']['role_assignments'] = 0

        # Log the deletion BEFORE deleting the user
        AuditLog.objects.create(
            user=request.user,
            action_type='user_deletion',
            description=f'PERMANENTLY DELETED user account and ALL related data: {user_info}. Summary: {deletion_summary}',
            related_object_type='CustomUser',
            related_object_id=user.id
        )

        # Send email notification about deletion
        try:
            send_system_notification_email(
                user=user,
                title="Account Deleted",
                message=f"Your account has been permanently deleted by an administrator. All your data has been removed from the system. If you believe this is an error, please contact support immediately.",
                notification_type="account_deletion"
            )
        except Exception as e:
            logger.error(f"Failed to send deletion email: {str(e)}")

        # FINALLY - Delete the user account (REAL DELETION)
        user.delete()

        return Response({
            'success': True,
            'message': f'User account {user_info} has been PERMANENTLY DELETED with all related data',
            'deletion_summary': deletion_summary
        })

    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to delete user'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# ADVANCED SEARCH & FILTERING SYSTEM
# ========================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_global_search(request):
    """Global search across all system data (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        query = request.GET.get('q', '').strip()
        search_type = request.GET.get('type', 'all')  # all, users, transactions, listings, reservations
        limit = int(request.GET.get('limit', 50))

        if not query:
            return Response({
                'success': False,
                'error': 'Search query is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        results = {
            'query': query,
            'search_type': search_type,
            'results': {
                'users': [],
                'transactions': [],
                'listings': [],
                'reservations': [],
                'notifications': []
            },
            'total_found': 0
        }

        # Search Users
        if search_type in ['all', 'users']:
            users = CustomUser.objects.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(phone_number__icontains=query)
            )[:limit]

            for user in users:
                results['results']['users'].append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': f"{user.first_name} {user.last_name}",
                    'user_type': user.user_type,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined
                })

        # Search Transactions
        if search_type in ['all', 'transactions']:
            transactions = Transaction.objects.filter(
                Q(transaction_id__icontains=query) |
                Q(reservation__listing__product_name__icontains=query) |
                Q(reservation__buyer__username__icontains=query) |
                Q(reservation__listing__farmer__username__icontains=query)
            )[:limit]

            for transaction in transactions:
                try:
                    results['results']['transactions'].append({
                        'transaction_id': transaction.transaction_id,
                        'amount': float(transaction.amount),
                        'status': transaction.status,
                        'farmer': transaction.reservation.listing.farmer.username,
                        'buyer': transaction.reservation.buyer.username,
                        'product': transaction.reservation.listing.product_name,
                        'created_at': transaction.created_at
                    })
                except Exception as e:
                    logger.error(f"Error serializing transaction in search: {str(e)}")
                    continue

        # Search Listings
        if search_type in ['all', 'listings']:
            listings = FarmerListing.objects.filter(
                Q(product_name__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query) |
                Q(farmer__username__icontains=query)
            )[:limit]

            for listing in listings:
                results['results']['listings'].append({
                    'id': listing.id,
                    'product_name': listing.product_name,
                    'farmer': listing.farmer.username,
                    'price': float(listing.price),
                    'quantity_available': listing.quantity_available,
                    'location': listing.location,
                    'status': listing.status,
                    'created_at': listing.created_at
                })

        # Search Reservations
        if search_type in ['all', 'reservations']:
            reservations = Reservation.objects.filter(
                Q(listing__product_name__icontains=query) |
                Q(buyer__username__icontains=query) |
                Q(listing__farmer__username__icontains=query) |
                Q(notes__icontains=query)
            )[:limit]

            for reservation in reservations:
                results['results']['reservations'].append({
                    'id': reservation.id,
                    'product': reservation.listing.product_name,
                    'farmer': reservation.listing.farmer.username,
                    'buyer': reservation.buyer.username,
                    'quantity': reservation.quantity,
                    'status': reservation.status,
                    'created_at': reservation.created_at
                })

        # Search Notifications
        if search_type in ['all', 'notifications']:
            notifications = Notification.objects.filter(
                Q(title__icontains=query) |
                Q(message__icontains=query) |
                Q(user__username__icontains=query)
            )[:limit]

            for notification in notifications:
                results['results']['notifications'].append({
                    'id': notification.notification_id,
                    'title': notification.title,
                    'message': notification.message[:100] + '...' if len(notification.message) > 100 else notification.message,
                    'user': notification.user.username,
                    'notification_type': notification.notification_type,
                    'is_read': notification.is_read,
                    'created_at': notification.created_at
                })

        # Calculate total results
        results['total_found'] = (
            len(results['results']['users']) +
            len(results['results']['transactions']) +
            len(results['results']['listings']) +
            len(results['results']['reservations']) +
            len(results['results']['notifications'])
        )

        return Response({
            'success': True,
            'search_results': results
        })

    except Exception as e:
        logger.error(f"Error in global search: {str(e)}")
        return Response({
            'success': False,
            'error': 'Search failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_advanced_filters(request):
    """Get advanced filtering options and statistics (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get filter options
        filter_options = {
            'user_types': [
                {'value': 'Farmer', 'label': 'Farmers', 'count': CustomUser.objects.filter(user_type='Farmer').count()},
                {'value': 'Buyer', 'label': 'Buyers', 'count': CustomUser.objects.filter(user_type='Buyer').count()},
                {'value': 'Admin', 'label': 'Admins', 'count': CustomUser.objects.filter(user_type='Admin').count()}
            ],
            'user_statuses': [
                {'value': True, 'label': 'Active', 'count': CustomUser.objects.filter(is_active=True).count()},
                {'value': False, 'label': 'Inactive', 'count': CustomUser.objects.filter(is_active=False).count()}
            ],
            'approval_statuses': [
                {'value': True, 'label': 'Approved', 'count': CustomUser.objects.filter(is_approved=True).count()},
                {'value': False, 'label': 'Pending Approval', 'count': CustomUser.objects.filter(is_approved=False).count()}
            ],
            'transaction_statuses': [
                {'value': status[0], 'label': status[1], 'count': Transaction.objects.filter(status=status[0]).count()}
                for status in Transaction.STATUS_CHOICES
            ],
            'reservation_statuses': [
                {'value': status[0], 'label': status[1], 'count': Reservation.objects.filter(status=status[0]).count()}
                for status in Reservation.STATUS_CHOICES
            ],
            'listing_statuses': [
                {'value': status[0], 'label': status[1], 'count': FarmerListing.objects.filter(status=status[0]).count()}
                for status in FarmerListing.STATUS_CHOICES
            ],
            'categories': []
        }

        # Get categories
        categories = Category.objects.all()
        for category in categories:
            filter_options['categories'].append({
                'value': category.id,
                'label': category.name,
                'count': FarmerListing.objects.filter(category=category).count()
            })

        # Get date ranges
        from datetime import datetime, timedelta
        now = datetime.now()

        date_ranges = {
            'today': {
                'label': 'Today',
                'users': CustomUser.objects.filter(date_joined__date=now.date()).count(),
                'transactions': Transaction.objects.filter(created_at__date=now.date()).count(),
                'listings': FarmerListing.objects.filter(created_at__date=now.date()).count()
            },
            'week': {
                'label': 'This Week',
                'users': CustomUser.objects.filter(date_joined__gte=now - timedelta(days=7)).count(),
                'transactions': Transaction.objects.filter(created_at__gte=now - timedelta(days=7)).count(),
                'listings': FarmerListing.objects.filter(created_at__gte=now - timedelta(days=7)).count()
            },
            'month': {
                'label': 'This Month',
                'users': CustomUser.objects.filter(date_joined__gte=now - timedelta(days=30)).count(),
                'transactions': Transaction.objects.filter(created_at__gte=now - timedelta(days=30)).count(),
                'listings': FarmerListing.objects.filter(created_at__gte=now - timedelta(days=30)).count()
            }
        }

        # Get location statistics
        farmer_locations = CustomUser.objects.filter(
            user_type='Farmer',
            farmerprofile__location__isnull=False
        ).values_list('farmerprofile__location', flat=True).distinct()

        buyer_locations = CustomUser.objects.filter(
            user_type='Buyer',
            buyerprofile__location__isnull=False
        ).values_list('buyerprofile__location', flat=True).distinct()

        location_stats = {
            'farmer_locations': list(farmer_locations),
            'buyer_locations': list(buyer_locations),
            'total_unique_locations': len(set(list(farmer_locations) + list(buyer_locations)))
        }

        return Response({
            'success': True,
            'filter_options': filter_options,
            'date_ranges': date_ranges,
            'location_stats': location_stats
        })

    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get filter options'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# ROLE-BASED ACCESS CONTROL SYSTEM
# ========================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_roles_list(request):
    """Get all available admin roles (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        from .models import AdminRole
        roles = AdminRole.objects.filter(is_active=True)

        roles_data = []
        for role in roles:
            roles_data.append({
                'id': role.id,
                'name': role.name,
                'display_name': role.display_name,
                'description': role.description,
                'permissions': role.permissions,
                'is_active': role.is_active,
                'created_at': role.created_at
            })

        return Response({
            'success': True,
            'roles': roles_data
        })

    except Exception as e:
        logger.error(f"Error getting admin roles: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get admin roles'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def assign_admin_role(request):
    """Assign role to admin user (Superuser only)"""
    try:
        if not request.user.is_superuser:
            return Response({
                'success': False,
                'error': 'Superuser access required'
            }, status=status.HTTP_403_FORBIDDEN)

        admin_user_id = request.data.get('admin_user_id')
        role_id = request.data.get('role_id')

        if not admin_user_id or not role_id:
            return Response({
                'success': False,
                'error': 'admin_user_id and role_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get admin user
        try:
            admin_user = CustomUser.objects.get(id=admin_user_id, user_type='Admin')
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Admin user not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get role
        try:
            from .models import AdminRole
            role = AdminRole.objects.get(id=role_id, is_active=True)
        except AdminRole.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Role not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Create or update role assignment
        from .models import AdminRoleAssignment
        assignment, created = AdminRoleAssignment.objects.get_or_create(
            admin_user=admin_user,
            role=role,
            defaults={
                'assigned_by': request.user,
                'is_active': True
            }
        )

        if not created:
            assignment.is_active = True
            assignment.assigned_by = request.user
            assignment.assigned_at = timezone.now()
            assignment.save()

        # Log the assignment
        AuditLog.objects.create(
            user=request.user,
            action_type='admin_action',
            description=f'Assigned role "{role.display_name}" to admin {admin_user.username}',
            related_object_type='AdminRoleAssignment',
            related_object_id=assignment.id
        )

        # Send notification
        Notification.objects.create(
            user=admin_user,
            title="Role Assigned",
            message=f"You have been assigned the role: {role.display_name}",
            notification_type="role_assignment"
        )

        return Response({
            'success': True,
            'message': f'Role "{role.display_name}" assigned to {admin_user.username}',
            'assignment': {
                'id': assignment.id,
                'admin_user': admin_user.username,
                'role': role.display_name,
                'assigned_by': request.user.username,
                'assigned_at': assignment.assigned_at
            }
        })

    except Exception as e:
        logger.error(f"Error assigning admin role: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to assign role'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_user_roles(request, admin_user_id):
    """Get roles assigned to specific admin user (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            admin_user = CustomUser.objects.get(id=admin_user_id, user_type='Admin')
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Admin user not found'
            }, status=status.HTTP_404_NOT_FOUND)

        from .models import AdminRoleAssignment
        assignments = AdminRoleAssignment.objects.filter(
            admin_user=admin_user,
            is_active=True
        ).select_related('role', 'assigned_by')

        roles_data = []
        for assignment in assignments:
            roles_data.append({
                'assignment_id': assignment.id,
                'role': {
                    'id': assignment.role.id,
                    'name': assignment.role.name,
                    'display_name': assignment.role.display_name,
                    'description': assignment.role.description,
                    'permissions': assignment.role.permissions
                },
                'assigned_by': assignment.assigned_by.username,
                'assigned_at': assignment.assigned_at
            })

        return Response({
            'success': True,
            'admin_user': {
                'id': admin_user.id,
                'username': admin_user.username,
                'email': admin_user.email,
                'full_name': f"{admin_user.first_name} {admin_user.last_name}"
            },
            'roles': roles_data
        })

    except Exception as e:
        logger.error(f"Error getting admin user roles: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get admin user roles'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_admin_role(request, assignment_id):
    """Remove role from admin user (Superuser only)"""
    try:
        if not request.user.is_superuser:
            return Response({
                'success': False,
                'error': 'Superuser access required'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            from .models import AdminRoleAssignment
            assignment = AdminRoleAssignment.objects.get(id=assignment_id)
        except AdminRoleAssignment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Role assignment not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Store info for logging
        admin_user = assignment.admin_user
        role = assignment.role

        # Deactivate assignment
        assignment.is_active = False
        assignment.save()

        # Log the removal
        AuditLog.objects.create(
            user=request.user,
            action_type='admin_action',
            description=f'Removed role "{role.display_name}" from admin {admin_user.username}',
            related_object_type='AdminRoleAssignment',
            related_object_id=assignment.id
        )

        # Send notification
        Notification.objects.create(
            user=admin_user,
            title="Role Removed",
            message=f"The role '{role.display_name}' has been removed from your account.",
            notification_type="role_removal"
        )

        return Response({
            'success': True,
            'message': f'Role "{role.display_name}" removed from {admin_user.username}'
        })

    except Exception as e:
        logger.error(f"Error removing admin role: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to remove role'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def check_admin_permission(user, permission):
    """Helper function to check if admin has specific permission"""
    if not user.is_authenticated or user.user_type != 'Admin':
        return False

    # Superusers have all permissions
    if user.is_superuser:
        return True

    try:
        from .models import AdminRoleAssignment
        assignments = AdminRoleAssignment.objects.filter(
            admin_user=user,
            is_active=True
        ).select_related('role')

        for assignment in assignments:
            role_permissions = assignment.role.permissions
            if permission in role_permissions and role_permissions[permission]:
                return True

        return False
    except Exception:
        return False


# ========================================
# ENHANCED ADMIN DASHBOARD ANALYTICS
# ========================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_enhanced_analytics(request):
    """Get comprehensive system analytics (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        from datetime import datetime, timedelta
        from django.db.models import Count, Sum, Avg

        now = datetime.now()

        # Time periods
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        year_ago = now - timedelta(days=365)

        # User Analytics
        user_stats = {
            'total_users': CustomUser.objects.count(),
            'farmers': CustomUser.objects.filter(user_type='Farmer').count(),
            'buyers': CustomUser.objects.filter(user_type='Buyer').count(),
            'admins': CustomUser.objects.filter(user_type='Admin').count(),
            'active_users': CustomUser.objects.filter(is_active=True).count(),
            'pending_farmers': CustomUser.objects.filter(user_type='Farmer', is_approved=False).count(),
            'new_users_today': CustomUser.objects.filter(date_joined__date=today).count(),
            'new_users_week': CustomUser.objects.filter(date_joined__gte=week_ago).count(),
            'new_users_month': CustomUser.objects.filter(date_joined__gte=month_ago).count()
        }

        # Transaction Analytics
        transaction_stats = {
            'total_transactions': Transaction.objects.count(),
            'successful_transactions': Transaction.objects.filter(status='Successful').count(),
            'pending_transactions': Transaction.objects.filter(status='Pending').count(),
            'failed_transactions': Transaction.objects.filter(status='Failed').count(),
            'total_revenue': float(Transaction.objects.filter(status='Successful').aggregate(Sum('amount'))['amount__sum'] or 0),
            'avg_transaction_amount': float(Transaction.objects.filter(status='Successful').aggregate(Avg('amount'))['amount__avg'] or 0),
            'transactions_today': Transaction.objects.filter(created_at__date=today).count(),
            'transactions_week': Transaction.objects.filter(created_at__gte=week_ago).count(),
            'transactions_month': Transaction.objects.filter(created_at__gte=month_ago).count(),
            'revenue_today': float(Transaction.objects.filter(created_at__date=today, status='Successful').aggregate(Sum('amount'))['amount__sum'] or 0),
            'revenue_week': float(Transaction.objects.filter(created_at__gte=week_ago, status='Successful').aggregate(Sum('amount'))['amount__sum'] or 0),
            'revenue_month': float(Transaction.objects.filter(created_at__gte=month_ago, status='Successful').aggregate(Sum('amount'))['amount__sum'] or 0)
        }

        # Listing Analytics
        listing_stats = {
            'total_listings': FarmerListing.objects.count(),
            'available_listings': FarmerListing.objects.filter(status='Available').count(),
            'sold_listings': FarmerListing.objects.filter(status='Sold').count(),
            'expired_listings': FarmerListing.objects.filter(status='Expired').count(),
            'listings_today': FarmerListing.objects.filter(created_at__date=today).count(),
            'listings_week': FarmerListing.objects.filter(created_at__gte=week_ago).count(),
            'listings_month': FarmerListing.objects.filter(created_at__gte=month_ago).count()
        }

        # Reservation Analytics
        reservation_stats = {
            'total_reservations': Reservation.objects.count(),
            'pending_reservations': Reservation.objects.filter(status='Pending').count(),
            'approved_reservations': Reservation.objects.filter(status='Approved').count(),
            'rejected_reservations': Reservation.objects.filter(status='Rejected').count(),
            'reservations_today': Reservation.objects.filter(created_at__date=today).count(),
            'reservations_week': Reservation.objects.filter(created_at__gte=week_ago).count(),
            'reservations_month': Reservation.objects.filter(created_at__gte=month_ago).count()
        }

        # Category Analytics
        category_stats = []
        categories = Category.objects.all()
        for category in categories:
            listings_count = FarmerListing.objects.filter(category=category).count()
            category_stats.append({
                'category': category.name,
                'listings_count': listings_count,
                'active_listings': FarmerListing.objects.filter(category=category, status='Available').count()
            })

        # Top Farmers (by listings)
        top_farmers = []
        farmers = CustomUser.objects.filter(user_type='Farmer', is_active=True)[:10]
        for farmer in farmers:
            listings_count = FarmerListing.objects.filter(farmer=farmer).count()
            successful_transactions = Transaction.objects.filter(
                reservation__listing__farmer=farmer,
                status='Successful'
            ).count()
            total_revenue = float(Transaction.objects.filter(
                reservation__listing__farmer=farmer,
                status='Successful'
            ).aggregate(Sum('amount'))['amount__sum'] or 0)

            top_farmers.append({
                'farmer_id': farmer.id,
                'username': farmer.username,
                'full_name': f"{farmer.first_name} {farmer.last_name}",
                'listings_count': listings_count,
                'successful_transactions': successful_transactions,
                'total_revenue': total_revenue
            })

        # Sort by revenue
        top_farmers.sort(key=lambda x: x['total_revenue'], reverse=True)
        top_farmers = top_farmers[:5]

        # Top Buyers (by transactions)
        top_buyers = []
        buyers = CustomUser.objects.filter(user_type='Buyer', is_active=True)[:10]
        for buyer in buyers:
            transactions_count = Transaction.objects.filter(
                reservation__buyer=buyer,
                status='Successful'
            ).count()
            total_spent = float(Transaction.objects.filter(
                reservation__buyer=buyer,
                status='Successful'
            ).aggregate(Sum('amount'))['amount__sum'] or 0)

            top_buyers.append({
                'buyer_id': buyer.id,
                'username': buyer.username,
                'full_name': f"{buyer.first_name} {buyer.last_name}",
                'transactions_count': transactions_count,
                'total_spent': total_spent
            })

        # Sort by spending
        top_buyers.sort(key=lambda x: x['total_spent'], reverse=True)
        top_buyers = top_buyers[:5]

        # Recent Activity
        recent_activities = []

        # Recent users
        recent_users = CustomUser.objects.filter(date_joined__gte=week_ago).order_by('-date_joined')[:5]
        for user in recent_users:
            recent_activities.append({
                'type': 'user_registration',
                'description': f"New {user.user_type.lower()} registered: {user.username}",
                'timestamp': user.date_joined,
                'user': user.username
            })

        # Recent transactions
        recent_transactions = Transaction.objects.filter(created_at__gte=week_ago).order_by('-created_at')[:5]
        for transaction in recent_transactions:
            recent_activities.append({
                'type': 'transaction',
                'description': f"Transaction {transaction.transaction_id}: {transaction.status}",
                'timestamp': transaction.created_at,
                'amount': float(transaction.amount)
            })

        # Sort by timestamp
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_activities = recent_activities[:10]

        return Response({
            'success': True,
            'analytics': {
                'user_stats': user_stats,
                'transaction_stats': transaction_stats,
                'listing_stats': listing_stats,
                'reservation_stats': reservation_stats,
                'category_stats': category_stats,
                'top_farmers': top_farmers,
                'top_buyers': top_buyers,
                'recent_activities': recent_activities,
                'generated_at': now
            }
        })

    except Exception as e:
        logger.error(f"Error getting enhanced analytics: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get analytics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# REAL-TIME NOTIFICATION SYSTEM
# ========================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_notifications(request):
    """Get all notifications for the authenticated user"""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'

        # Get notifications
        notifications = Notification.objects.filter(user=request.user)

        if unread_only:
            notifications = notifications.filter(is_read=False)

        notifications = notifications.order_by('-created_at')

        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(notifications, per_page)
        page_obj = paginator.get_page(page)

        # Serialize notifications
        notifications_data = []
        for notification in page_obj:
            notifications_data.append({
                'id': notification.notification_id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at,
                'read_at': notification.read_at
            })

        # Get unread count
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return Response({
            'success': True,
            'notifications': notifications_data,
            'unread_count': unread_count,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_notifications': paginator.count,
                'per_page': per_page,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })

    except Exception as e:
        logger.error(f"Error getting user notifications: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get notifications'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    try:
        notification = Notification.objects.get(
            notification_id=notification_id,
            user=request.user
        )

        notification.is_read = True
        notification.save()

        # Get updated unread count
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return Response({
            'success': True,
            'message': 'Notification marked as read',
            'unread_count': unread_count
        })

    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to mark notification as read'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read for the authenticated user"""
    try:
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({
            'success': True,
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count,
            'unread_count': 0
        })

    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to mark all notifications as read'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_notification(request, notification_id):
    """Delete a specific notification"""
    try:
        notification = Notification.objects.get(
            notification_id=notification_id,
            user=request.user
        )

        notification.delete()

        # Get updated unread count
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return Response({
            'success': True,
            'message': 'Notification deleted',
            'unread_count': unread_count
        })

    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to delete notification'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_notification_count(request):
    """Get unread notification count for the authenticated user"""
    try:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        total_count = Notification.objects.filter(user=request.user).count()

        return Response({
            'success': True,
            'unread_count': unread_count,
            'total_count': total_count
        })

    except Exception as e:
        logger.error(f"Error getting notification count: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get notification count'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# ADMIN BROADCAST SYSTEM
# ========================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_broadcast_notification(request):
    """Send broadcast notification to users (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        title = request.data.get('title')
        message = request.data.get('message')
        target_group = request.data.get('target_group', 'all')  # all, farmers, buyers, admins
        send_email = request.data.get('send_email', False)
        urgent = request.data.get('urgent', False)

        if not title or not message:
            return Response({
                'success': False,
                'error': 'Title and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get target users
        if target_group == 'farmers':
            target_users = CustomUser.objects.filter(user_type='Farmer', is_active=True)
        elif target_group == 'buyers':
            target_users = CustomUser.objects.filter(user_type='Buyer', is_active=True)
        elif target_group == 'admins':
            target_users = CustomUser.objects.filter(user_type='Admin', is_active=True)
        else:  # all
            target_users = CustomUser.objects.filter(is_active=True)

        # Create notifications for all target users
        notifications_created = 0
        emails_sent = 0

        notification_type = "urgent_announcement" if urgent else "system_announcement"

        for user in target_users:
            # Create in-app notification
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type
            )
            notifications_created += 1

            # Send email if requested
            if send_email:
                try:
                    send_system_notification_email(
                        user=user,
                        title=title,
                        message=message,
                        notification_type=notification_type
                    )
                    emails_sent += 1
                except Exception as e:
                    logger.error(f"Failed to send broadcast email to {user.email}: {str(e)}")

        # Log the broadcast
        AuditLog.objects.create(
            user=request.user,
            action_type='admin_broadcast',
            description=f'Sent broadcast "{title}" to {target_group} ({notifications_created} users). Emails sent: {emails_sent}',
            related_object_type='Notification',
            related_object_id=None
        )

        return Response({
            'success': True,
            'message': f'Broadcast sent successfully to {notifications_created} users',
            'details': {
                'title': title,
                'target_group': target_group,
                'notifications_created': notifications_created,
                'emails_sent': emails_sent,
                'urgent': urgent,
                'sent_by': f"{request.user.first_name} {request.user.last_name}"
            }
        })

    except Exception as e:
        logger.error(f"Error sending broadcast notification: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to send broadcast notification'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_send_individual_notification(request):
    """Send notification to specific user (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        title = request.data.get('title')
        message = request.data.get('message')
        send_email = request.data.get('send_email', False)
        urgent = request.data.get('urgent', False)

        if not all([user_id, title, message]):
            return Response({
                'success': False,
                'error': 'user_id, title, and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get target user
        try:
            target_user = CustomUser.objects.get(id=user_id, is_active=True)
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found or inactive'
            }, status=status.HTTP_404_NOT_FOUND)

        notification_type = "urgent_notification" if urgent else "admin_message"

        # Create notification
        notification = Notification.objects.create(
            user=target_user,
            title=title,
            message=message,
            notification_type=notification_type
        )

        # Send email if requested
        email_sent = False
        if send_email:
            try:
                send_system_notification_email(
                    user=target_user,
                    title=title,
                    message=message,
                    notification_type=notification_type
                )
                email_sent = True
            except Exception as e:
                logger.error(f"Failed to send notification email to {target_user.email}: {str(e)}")

        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action_type='admin_notification',
            description=f'Sent notification "{title}" to user {target_user.username} ({target_user.email})',
            related_object_type='Notification',
            related_object_id=notification.id
        )

        return Response({
            'success': True,
            'message': f'Notification sent to {target_user.username}',
            'details': {
                'notification_id': notification.notification_id,
                'title': title,
                'target_user': target_user.username,
                'email_sent': email_sent,
                'urgent': urgent,
                'sent_by': f"{request.user.first_name} {request.user.last_name}"
            }
        })

    except Exception as e:
        logger.error(f"Error sending individual notification: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to send notification'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_broadcast_history(request):
    """Get history of admin broadcasts (Admin only)"""
    try:
        if request.user.user_type != 'Admin':
            return Response({
                'success': False,
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))

        # Get broadcast audit logs
        broadcasts = AuditLog.objects.filter(
            action_type__in=['admin_broadcast', 'admin_notification']
        ).order_by('-created_at')

        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(broadcasts, per_page)
        page_obj = paginator.get_page(page)

        # Serialize broadcast history
        broadcast_history = []
        for log in page_obj:
            broadcast_history.append({
                'id': log.id,
                'action_type': log.action_type,
                'description': log.description,
                'sent_by': log.user.username,
                'sent_by_name': f"{log.user.first_name} {log.user.last_name}",
                'created_at': log.created_at
            })

        return Response({
            'success': True,
            'broadcast_history': broadcast_history,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_broadcasts': paginator.count,
                'per_page': per_page,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })

    except Exception as e:
        logger.error(f"Error getting broadcast history: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get broadcast history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# FRONTEND SERVING VIEWS
# =============================================================================

def home_view(request):
    """Serve the main landing page"""
    return render(request, 'index.html')

def admin_login_view(request):
    """Serve admin login page"""
    return render(request, 'Admin/admin_login.html')

def farmer_login_view(request):
    """Serve farmer login page"""
    return render(request, 'Farmer/loginfarmer.html')

def buyer_login_view(request):
    """Serve buyer login page"""
    return render(request, 'Buyer/loginbuyer.html')

def farmer_signup_view(request):
    """Serve farmer signup page"""
    return render(request, 'Farmer/signupfarmer.html')

def buyer_signup_view(request):
    """Serve buyer signup page"""
    return render(request, 'Buyer/signupbuyer.html')

def marketplace_view(request):
    """Serve marketplace page"""
    return render(request, 'Buyer/marketplace.html')

def admin_dashboard_view(request):
    """Serve admin dashboard page"""
    return render(request, 'Admin/admin_dashboard.html')

def farmer_dashboard_view(request):
    """Serve farmer dashboard page"""
    return render(request, 'Farmer/farmer dashboard.html')

def buyer_dashboard_view(request):
    """Serve buyer dashboard page"""
    return render(request, 'Buyer/buyerdashboard.html')
