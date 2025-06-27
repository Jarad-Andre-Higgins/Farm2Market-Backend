"""
Email utility functions for Agriport
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_buyer_welcome_email(user, password, verification_token, request):
    """
    Send welcome email to new buyer with login credentials and verification link
    """
    try:
        # Email context
        context = {
            'user': user,
            'password': password,
            'verification_token': verification_token,
            'verification_url': f"{request.build_absolute_uri('/')[:-1]}/verify-email/{verification_token}/",
            'login_url': f"{request.build_absolute_uri('/')[:-1]}/loginbuyer.html",
            'request': request
        }
        
        # Render HTML email template
        html_message = render_to_string('emails/buyer_welcome.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Welcome to Farm2Market - Your Account Details',
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {e}")
        return False


def send_password_reset_email(user, reset_token, request):
    """
    Send password reset email to buyer
    """
    try:
        # Create reset URL that points to the frontend reset page with token parameter
        base_url = request.build_absolute_uri('/')[:-1]
        reset_url = f"{base_url}/Frontend/Buyer/reset-password.html?token={reset_token}"
        
        # Email context
        context = {
            'user': user,
            'reset_url': reset_url,
            'reset_token': reset_token,
            'request': request
        }
        
        # Render HTML email template
        html_message = render_to_string('emails/password_reset.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Farm2Market - Password Reset Request',
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        return False


def send_email_verification(user, verification_token, request):
    """
    Send email verification to buyer
    """
    try:
        verification_url = f"{request.build_absolute_uri('/')[:-1]}/verify-email/{verification_token}/"
        
        # Email context
        context = {
            'user': user,
            'verification_url': verification_url,
            'verification_token': verification_token,
            'request': request
        }
        
        # Render HTML email template
        html_message = render_to_string('emails/email_verification.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Farm2Market - Verify Your Email Address',
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Email verification sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email verification to {user.email}: {e}")
        return False


def send_buyer_notification_email(user, subject, message, request=None):
    """
    Send general notification email to buyer
    """
    try:
        # Simple text email for notifications
        send_mail(
            subject=f"Agriport - {subject}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"Notification email sent successfully to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send notification email to {user.email}: {e}")
        return False


def send_farmer_registration_email(user, password=None):
    """Send registration confirmation email to farmer"""
    try:
        subject = 'Welcome to Agriport - Farmer Registration Submitted'

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2c3e50;">🌱 Welcome to Agriport</h1>
                    <h2 style="color: #27ae60;">Farmer Registration Submitted</h2>
                </div>

                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="color: #27ae60;">Thank you for registering!</h2>
                    <p>Dear {user.first_name} {user.last_name},</p>
                    <p>Your farmer registration has been submitted successfully and is currently under review by our admin team.</p>
                </div>

                <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #1976d2;">📋 Your Registration Details:</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Name:</strong> {user.first_name} {user.last_name}</li>
                        <li><strong>Email:</strong> {user.email}</li>
                        <li><strong>Username:</strong> {user.username}</li>
                        <li><strong>Phone:</strong> {user.phone_number or 'Not provided'}</li>
                        <li><strong>Registration Date:</strong> {user.date_joined.strftime('%B %d, %Y')}</li>
                    </ul>
                </div>

                <div style="background: #fff3cd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #856404;">⏳ What's Next?</h3>
                    <p>Our admin team will review your application within 24-48 hours. You will receive an email notification once your account is approved.</p>
                    <p>Once approved, you'll be able to:</p>
                    <ul>
                        <li>✅ List your agricultural products</li>
                        <li>✅ Connect with buyers</li>
                        <li>✅ Manage your farm inventory</li>
                        <li>✅ Track sales and reservations</li>
                        <li>✅ Communicate with customers</li>
                    </ul>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #7f8c8d;">Thank you for choosing Agriport!</p>
                    <p style="color: #7f8c8d;"><strong>The Agriport Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_message = f"""
        Welcome to Agriport!

        Dear {user.first_name} {user.last_name},

        Thank you for registering as a farmer on Agriport. Your registration has been submitted and is currently under review by our admin team.

        Registration Details:
        - Name: {user.first_name} {user.last_name}
        - Email: {user.email}
        - Username: {user.username}
        - Phone: {user.phone_number or 'Not provided'}
        - Registration Date: {user.date_joined.strftime('%B %d, %Y')}

        What's Next?
        Our admin team will review your application within 24-48 hours. You will receive an email notification once your account is approved.

        Thank you for choosing Agriport!
        The Agriport Team
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Farmer registration email sent successfully to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send farmer registration email: {str(e)}")
        return False


def send_farmer_approval_email(user, approved=True, admin_user=None):
    """Send approval/rejection email to farmer"""
    try:
        if approved:
            subject = 'Agriport - Account Approved! 🎉'

            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #2c3e50;">🌱 Agriport</h1>
                        <h2 style="color: #27ae60;">🎉 Account Approved!</h2>
                    </div>

                    <div style="background: #d4edda; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <h2 style="color: #155724;">Congratulations!</h2>
                        <p>Dear {user.first_name} {user.last_name},</p>
                        <p>Great news! Your farmer account on Agriport has been approved and is now active.</p>
                    </div>

                    <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <h3 style="color: #1976d2;">🔑 Your Login Details:</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Email:</strong> {user.email}</li>
                            <li><strong>Username:</strong> {user.username}</li>
                            <li><strong>Login URL:</strong> <a href="http://localhost:8000/Frontend/Farmer/loginfarmer.html">Farmer Login</a></li>
                        </ul>
                    </div>

                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <h3 style="color: #495057;">🚀 You can now:</h3>
                        <ul>
                            <li>✅ Login to your farmer dashboard</li>
                            <li>✅ Add and manage your products</li>
                            <li>✅ Handle reservations from buyers</li>
                            <li>✅ Communicate with customers</li>
                            <li>✅ Track your sales and earnings</li>
                            <li>✅ Update your farm profile</li>
                        </ul>
                    </div>

                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #7f8c8d;">Welcome to the Agriport farming community!</p>
                        <p style="color: #7f8c8d;"><strong>The Agriport Team</strong></p>
                    </div>
                </div>
            </body>
            </html>
            """

            plain_message = f"""
            Congratulations! Your Agriport Account is Approved!

            Dear {user.first_name} {user.last_name},

            Great news! Your farmer account on Agriport has been approved and is now active.

            Login Details:
            Email: {user.email}
            Username: {user.username}
            Login URL: http://localhost:8000/Frontend/Farmer/loginfarmer.html

            You can now:
            - Login to your farmer dashboard
            - Add and manage your products
            - Handle reservations from buyers
            - Communicate with customers
            - Track your sales and earnings
            - Update your farm profile

            Welcome to the Agriport farming community!
            The Agriport Team
            """
        else:
            subject = 'Agriport - Account Application Update'

            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #2c3e50;">🌱 Agriport</h1>
                        <h2 style="color: #dc3545;">Account Application Update</h2>
                    </div>

                    <div style="background: #f8d7da; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <p>Dear {user.first_name} {user.last_name},</p>
                        <p>Thank you for your interest in joining Agriport as a farmer. After careful review, we regret to inform you that your application has not been approved at this time.</p>
                    </div>

                    <div style="background: #fff3cd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <h3 style="color: #856404;">📞 Next Steps:</h3>
                        <p>If you believe this decision was made in error or if you have additional information to support your application, please contact our support team:</p>
                        <ul>
                            <li>Email: support@agriport.com</li>
                            <li>Phone: +1 (555) 123-4567</li>
                        </ul>
                        <p>You may also reapply in the future with updated information.</p>
                    </div>

                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #7f8c8d;">Thank you for your understanding.</p>
                        <p style="color: #7f8c8d;"><strong>The Agriport Team</strong></p>
                    </div>
                </div>
            </body>
            </html>
            """

            plain_message = f"""
            Agriport - Account Application Update

            Dear {user.first_name} {user.last_name},

            Thank you for your interest in joining Agriport as a farmer. After careful review, we regret to inform you that your application has not been approved at this time.

            Next Steps:
            If you believe this decision was made in error or if you have additional information to support your application, please contact our support team:

            Email: support@agriport.com
            Phone: +1 (555) 123-4567

            You may also reapply in the future with updated information.

            Thank you for your understanding.
            The Agriport Team
            """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Farmer {'approval' if approved else 'rejection'} email sent successfully to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send farmer {'approval' if approved else 'rejection'} email: {str(e)}")
        return False


def send_reservation_status_update_email(reservation, status_changed_by=None):
    """Send email when reservation status changes"""
    try:
        buyer = reservation.buyer
        farmer = reservation.listing.farmer
        product_name = reservation.listing.product_name

        if reservation.status == 'Approved':
            subject = f'Agriport - Reservation Approved for {product_name}'
            message_to_buyer = f"""
            Great news! Your reservation has been approved.

            Product: {product_name}
            Farmer: {farmer.first_name} {farmer.last_name}
            Quantity: {reservation.quantity}

            Please contact the farmer to arrange pickup/delivery.
            Farmer Contact: {farmer.email}
            """

        elif reservation.status == 'Rejected':
            subject = f'Agriport - Reservation Update for {product_name}'
            message_to_buyer = f"""
            We regret to inform you that your reservation has been declined.

            Product: {product_name}
            Farmer: {farmer.first_name} {farmer.last_name}
            Quantity: {reservation.quantity}

            Please browse other available products or contact the farmer for alternatives.
            """
        else:
            return True  # No email for other statuses

        # Send email to buyer
        send_mail(
            subject,
            message_to_buyer,
            settings.DEFAULT_FROM_EMAIL,
            [buyer.email],
            fail_silently=False,
        )

        logger.info(f"Reservation status email sent to buyer {buyer.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send reservation status email: {str(e)}")
        return False


def send_system_notification_email(user, title, message, notification_type="system"):
    """Send system notification email to user"""
    try:
        subject = f'Agriport - {title}'

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2c3e50;">🌱 Agriport</h1>
                    <h2 style="color: #3498db;">{title}</h2>
                </div>

                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <p>Dear {user.first_name} {user.last_name},</p>
                    <div style="margin: 20px 0;">
                        {message}
                    </div>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #7f8c8d;">This is an automated message from Agriport.</p>
                    <p style="color: #7f8c8d;"><strong>The Agriport Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_message = f"""
        Agriport - {title}

        Dear {user.first_name} {user.last_name},

        {message}

        This is an automated message from Agriport.
        The Agriport Team
        """

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"System notification email sent to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send system notification email: {str(e)}")
        return False


def send_admin_broadcast_email(users, title, message, sender_admin):
    """Send broadcast email to multiple users"""
    try:
        subject = f'Agriport Announcement - {title}'

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2c3e50;">🌱 Agriport</h1>
                    <h2 style="color: #e74c3c;">📢 System Announcement</h2>
                </div>

                <div style="background: #fff3cd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #856404;">{title}</h3>
                    <div style="margin: 20px 0;">
                        {message}
                    </div>
                </div>

                <div style="background: #e3f2fd; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                    <p style="margin: 0;"><strong>From:</strong> {sender_admin.first_name} {sender_admin.last_name} (Agriport Admin)</p>
                    <p style="margin: 5px 0 0 0;"><strong>Date:</strong> {timezone.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #7f8c8d;">This is an official announcement from Agriport administration.</p>
                    <p style="color: #7f8c8d;"><strong>The Agriport Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_message = f"""
        Agriport Announcement - {title}

        {message}

        From: {sender_admin.first_name} {sender_admin.last_name} (Agriport Admin)
        Date: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}

        This is an official announcement from Agriport administration.
        The Agriport Team
        """

        # Send to all users
        recipient_emails = [user.email for user in users if user.email]

        if recipient_emails:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_emails,
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Broadcast email sent to {len(recipient_emails)} users")
            return True
        else:
            logger.warning("No valid email addresses found for broadcast")
            return False

    except Exception as e:
        logger.error(f"Failed to send broadcast email: {str(e)}")
        return False


def send_reservation_confirmation_email(user, reservation, request):
    """
    Send reservation confirmation email to buyer
    """
    try:
        subject = f"Reservation Confirmation - {reservation.listing.product_name}"
        message = f"""
Dear {user.first_name} {user.last_name},

Your reservation has been confirmed!

Reservation Details:
- Product: {reservation.listing.product_name}
- Quantity: {reservation.quantity} {reservation.listing.unit}
- Price: {reservation.listing.price} FCFA per {reservation.listing.unit}
- Total: {reservation.listing.price * reservation.quantity} FCFA
- Farmer: {reservation.listing.farmer.get_full_name()}
- Status: {reservation.status}

Delivery Information:
- Method: {reservation.delivery_method}
- Location: {reservation.delivery_location}

Payment Information:
- Method: {reservation.payment_method}
- Status: {reservation.payment_status}

You can track your reservation status in your buyer dashboard.

Best regards,
Farm2Market Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Reservation confirmation email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send reservation confirmation email to {user.email}: {e}")
        return False


def send_reservation_status_update_email(user, reservation, request):
    """
    Send reservation status update email to buyer
    """
    try:
        status_message = {
            'Approved': 'approved',
            'Rejected': 'rejected',
            'Completed': 'completed',
            'Cancelled': 'cancelled'
        }.get(reservation.status, 'updated')
        
        subject = f"Reservation {status_message.title()} - {reservation.listing.product_name}"
        message = f"""
Dear {user.first_name} {user.last_name},

Your reservation for {reservation.listing.product_name} has been {status_message}.

Reservation Details:
- Product: {reservation.listing.product_name}
- Quantity: {reservation.quantity} {reservation.listing.unit}
- Farmer: {reservation.listing.farmer.get_full_name()}
- New Status: {reservation.status}

{"Thank you for your purchase!" if reservation.status == 'Completed' else ""}
{"We apologize for any inconvenience." if reservation.status in ['Rejected', 'Cancelled'] else ""}

You can view more details in your buyer dashboard.

Best regards,
Farm2Market Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Reservation status update email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send reservation status update email to {user.email}: {e}")
        return False
