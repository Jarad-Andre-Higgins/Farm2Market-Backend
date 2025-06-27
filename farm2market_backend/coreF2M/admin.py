from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    CustomUser, FarmerProfile, BuyerProfile, Category,
    FarmerListing, ProductCategory, Reservation, UrgentSale,
    UrgentSaleReservation, Transaction, Notification, Review,
    Conversation, Message, MessageReadStatus, EmailVerificationToken,
    PasswordResetToken, FileUpload, SystemConfiguration, AuditLog
)

class CustomUserAdmin(UserAdmin):
    """Custom User Admin with approval functionality"""
    model = CustomUser
    list_display = ['email', 'username', 'user_type', 'is_approved', 'is_active', 'date_joined', 'approval_actions']
    list_filter = ['user_type', 'is_approved', 'is_active', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'is_approved')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'user_type', 'phone_number', 'is_approved')
        }),
    )

    def approval_actions(self, obj):
        """Custom approval action buttons"""
        if obj.user_type == 'Farmer' and not obj.is_approved:
            approve_url = reverse('admin:approve_farmer', args=[obj.pk])
            reject_url = reverse('admin:reject_farmer', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Approve</a>&nbsp;'
                '<a class="button" href="{}">Reject</a>',
                approve_url, reject_url
            )
        elif obj.user_type == 'Farmer' and obj.is_approved:
            return format_html('<span style="color: green;">✓ Approved</span>')
        else:
            return '-'
    approval_actions.short_description = 'Actions'

    def get_urls(self):
        """Add custom URLs for approval actions"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('approve-farmer/<int:user_id>/', self.admin_site.admin_view(self.approve_farmer), name='approve_farmer'),
            path('reject-farmer/<int:user_id>/', self.admin_site.admin_view(self.reject_farmer), name='reject_farmer'),
        ]
        return custom_urls + urls

    def approve_farmer(self, request, user_id):
        """Approve farmer and send email notification"""
        try:
            user = CustomUser.objects.get(pk=user_id, user_type='Farmer')
            user.is_approved = True
            user.save()

            # Send approval email
            self.send_approval_email(user, approved=True)

            # Create notification
            Notification.objects.create(
                user=user,
                title="Account Approved!",
                message="Congratulations! Your farmer account has been approved. You can now start listing your products.",
                notification_type="system_announcement"
            )

            messages.success(request, f'Farmer {user.username} has been approved successfully!')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Farmer not found.')

        return HttpResponseRedirect(reverse('admin:coreF2M_customuser_changelist'))

    def reject_farmer(self, request, user_id):
        """Reject farmer and send email notification"""
        try:
            user = CustomUser.objects.get(pk=user_id, user_type='Farmer')

            # Send rejection email
            self.send_approval_email(user, approved=False)

            # Create notification
            Notification.objects.create(
                user=user,
                title="Account Application Update",
                message="We're sorry, but your farmer account application has been rejected. Please contact support for more information.",
                notification_type="system_announcement"
            )

            # Optionally delete the user or keep for records
            # user.delete()  # Uncomment if you want to delete rejected farmers

            messages.warning(request, f'Farmer {user.username} has been rejected.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Farmer not found.')

        return HttpResponseRedirect(reverse('admin:coreF2M_customuser_changelist'))

    def send_approval_email(self, user, approved=True):
        """Send email notification for approval/rejection"""
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
            print(f"Failed to send email to {user.email}: {e}")

class FarmerProfileAdmin(admin.ModelAdmin):
    """Farmer Profile Admin"""
    list_display = ['farmer', 'location', 'trust_badge']
    list_filter = ['trust_badge']
    search_fields = ['farmer__username', 'farmer__email', 'location']

class CategoryAdmin(admin.ModelAdmin):
    """Category Admin"""
    list_display = ['category_id', 'name']
    search_fields = ['name']

class FarmerListingAdmin(admin.ModelAdmin):
    """Farmer Listing Admin"""
    list_display = ['listing_id', 'farmer', 'product_name', 'price', 'quantity', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['product_name', 'farmer__username']
    ordering = ['-created_at']

class ReservationAdmin(admin.ModelAdmin):
    """Reservation Admin"""
    list_display = ['reservation_id', 'buyer', 'listing', 'quantity', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['buyer__username', 'listing__product_name']
    ordering = ['-created_at']

class NotificationAdmin(admin.ModelAdmin):
    """Enhanced Notification Admin"""
    list_display = ['notification_id', 'user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'read_at']

    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

# Register models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(FarmerProfile, FarmerProfileAdmin)
# BuyerProfile now uses @admin.register decorator
admin.site.register(Category, CategoryAdmin)
admin.site.register(FarmerListing, FarmerListingAdmin)
admin.site.register(ProductCategory)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(UrgentSale)
admin.site.register(UrgentSaleReservation)
admin.site.register(Transaction)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Review)

# Chat Models
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['conversation_id', 'get_participants', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['participants__username', 'participants__email']
    filter_horizontal = ['participants']

    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    get_participants.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'conversation', 'sender', 'content_preview', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'sender__user_type']
    search_fields = ['content', 'sender__username', 'conversation__conversation_id']
    readonly_fields = ['created_at', 'read_at']

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'read_at']
    list_filter = ['read_at', 'user__user_type']
    search_fields = ['user__username', 'message__content']


# Authentication Token Models
@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token_preview', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['token', 'created_at']

    def token_preview(self, obj):
        return f"{obj.token[:10]}..." if obj.token else ""
    token_preview.short_description = 'Token Preview'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token_preview', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['token', 'created_at']

    def token_preview(self, obj):
        return f"{obj.token[:10]}..." if obj.token else ""
    token_preview.short_description = 'Token Preview'


# Enhanced Buyer Profile Admin
@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'location', 'preferred_delivery_method', 'created_at']
    list_filter = ['preferred_delivery_method', 'created_at']
    search_fields = ['buyer__username', 'buyer__email', 'location']
    readonly_fields = ['created_at', 'updated_at']

# New Model Admins
@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ['file_id', 'uploaded_by', 'file_name', 'file_type', 'is_verified', 'created_at']
    list_filter = ['file_type', 'is_verified', 'created_at']
    search_fields = ['file_name', 'uploaded_by__username']
    readonly_fields = ['created_at', 'file_size', 'mime_type']


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ['config_key', 'config_value_preview', 'is_active', 'updated_at']
    list_filter = ['is_active', 'updated_at']
    search_fields = ['config_key', 'description']
    readonly_fields = ['created_at', 'updated_at']

    def config_value_preview(self, obj):
        return obj.config_value[:50] + '...' if len(obj.config_value) > 50 else obj.config_value
    config_value_preview.short_description = 'Value Preview'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['log_id', 'user', 'action_type', 'description_preview', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['user__username', 'description', 'action_type']
    readonly_fields = ['created_at', 'ip_address', 'user_agent']

    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description Preview'


# Customize admin site
admin.site.site_header = 'Farm2Market Administration'
admin.site.site_title = 'Farm2Market Admin'
admin.site.index_title = 'Welcome to Farm2Market Administration'
