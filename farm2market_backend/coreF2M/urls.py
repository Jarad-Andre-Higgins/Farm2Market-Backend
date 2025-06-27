from django.urls import path
from . import views

urlpatterns = [
    # API Root
    path('', views.api_root, name='api_root'),

    # Authentication
    path('auth/register/', views.register_user, name='register_user'),
    path('auth/login/', views.login_user, name='login_user'),
    
    # Categories
    path('categories/', views.categories_list, name='categories_list'),
    path('farmer/categories/', views.farmer_categories, name='farmer_categories'),
    path('farmer/categories/<int:category_id>/', views.farmer_category_detail, name='farmer_category_detail'),
    
    # Farmer Listings
    path('farmer/listings/', views.farmer_listings, name='farmer_listings'),
    path('farmer/<int:farmer_id>/listings/', views.public_farmer_listings, name='public_farmer_listings'),
    
    # Reservations
    path('reservations/create/', views.create_reservation, name='create_reservation'),
    path('farmer/reservations/', views.farmer_reservations, name='farmer_reservations'),
    path('reservations/<int:reservation_id>/status/', views.update_reservation_status, name='update_reservation_status'),
    
    # Urgent Sales
    path('farmer/urgent-sales/', views.urgent_sales, name='urgent_sales'),
    path('urgent-sales/public/', views.public_urgent_sales, name='public_urgent_sales'),
    
    # Notifications
    path('notifications/', views.user_notifications, name='user_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Profile
    path('farmer/profile/', views.farmer_profile, name='farmer_profile'),
    
    # Dashboard
    path('farmer/dashboard/', views.farmer_dashboard_data, name='farmer_dashboard_data'),
    
    # Search
    path('search/farmers/', views.search_farmers, name='search_farmers'),

    # Admin APIs
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/create-admin/', views.create_admin, name='create_admin'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/manage-users/', views.admin_manage_users, name='admin_manage_users'),
    path('admin/pending-farmers/', views.pending_farmers, name='pending_farmers'),
    path('admin/approve-farmer/<int:farmer_id>/', views.approve_farmer_api, name='approve_farmer_api'),
    path('admin/reject-farmer/<int:farmer_id>/', views.reject_farmer_api, name='reject_farmer_api'),

    # Admin CRUD Operations
    path('admin/view/<int:admin_id>/', views.admin_view_details, name='admin_view_details'),
    path('admin/update/<int:admin_id>/', views.admin_update, name='admin_update'),
    path('admin/delete/<int:admin_id>/', views.admin_delete, name='admin_delete'),

    # Transaction Management
    path('admin/transactions/', views.admin_transactions, name='admin_transactions'),
    path('admin/transactions/<str:transaction_id>/', views.admin_transaction_details, name='admin_transaction_details'),
    path('admin/transactions/<str:transaction_id>/update/', views.admin_update_transaction, name='admin_update_transaction'),

    # User Management
    path('admin/users/<int:user_id>/', views.admin_user_details, name='admin_user_details'),
    path('admin/users/<int:user_id>/update/', views.admin_update_user, name='admin_update_user'),
    path('admin/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),

    # Search & Filtering
    path('admin/search/', views.admin_global_search, name='admin_global_search'),
    path('admin/filters/', views.admin_advanced_filters, name='admin_advanced_filters'),

    # Role-Based Access Control
    path('admin/roles/', views.admin_roles_list, name='admin_roles_list'),
    path('admin/roles/assign/', views.assign_admin_role, name='assign_admin_role'),
    path('admin/users/<int:admin_user_id>/roles/', views.admin_user_roles, name='admin_user_roles'),
    path('admin/roles/remove/<int:assignment_id>/', views.remove_admin_role, name='remove_admin_role'),

    # Enhanced Analytics
    path('admin/analytics/', views.admin_enhanced_analytics, name='admin_enhanced_analytics'),

    # Notification System
    path('notifications/', views.get_user_notifications, name='get_user_notifications'),
    path('notifications/count/', views.get_notification_count, name='get_notification_count'),
    path('notifications/<str:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/<str:notification_id>/delete/', views.delete_notification, name='delete_notification'),

    # Admin Broadcast System
    path('admin/broadcast/', views.admin_broadcast_notification, name='admin_broadcast_notification'),
    path('admin/send-notification/', views.admin_send_individual_notification, name='admin_send_individual_notification'),
    path('admin/broadcast-history/', views.admin_broadcast_history, name='admin_broadcast_history'),

    # General Authentication APIs (for frontend compatibility)
    path('auth/login/', views.general_login, name='general_login'),
    path('auth/register/', views.general_register, name='general_register'),

    # Enhanced Chat/Messaging APIs
    path('messages/conversations/', views.get_conversations, name='get_conversations'),
    path('messages/conversation/<int:conversation_id>/', views.get_conversation_messages, name='get_conversation_messages'),
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/conversations/start/', views.start_conversation, name='start_conversation'),
    path('messages/conversations/<int:conversation_id>/read/', views.mark_conversation_read, name='mark_conversation_read'),
    path('messages/unread-count/', views.unread_messages_count, name='unread_messages_count'),
    path('messages/conversations/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('messages/search-users/', views.search_users_for_chat, name='search_users_for_chat'),

    # Receipt Upload System
    path('transactions/upload-receipt/', views.upload_receipt, name='upload_receipt'),
    path('transactions/<int:transaction_id>/verify-receipt/', views.verify_receipt, name='verify_receipt'),

    # Enhanced Notification APIs
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('messages/unread-count/', views.get_unread_messages_count, name='get_unread_messages_count'),

    # Buyer Authentication APIs
    path('buyer/register/', views.register_buyer, name='register_buyer'),
    path('buyer/login/', views.login_buyer, name='login_buyer'),
    path('buyer/verify-email/', views.verify_email, name='verify_email'),
    path('buyer/request-password-reset/', views.request_password_reset, name='request_password_reset'),
    path('buyer/reset-password/', views.reset_password, name='reset_password'),
    path('buyer/profile/', views.buyer_profile, name='buyer_profile'),
    path('buyer/dashboard-data/', views.buyer_dashboard_data, name='buyer_dashboard_data'),
    path('buyer/purchase-history/', views.buyer_purchase_history, name='buyer_purchase_history'),

    # Farmer Authentication APIs
    path('farmer/register/', views.register_farmer, name='register_farmer'),
    path('farmer/login/', views.login_farmer, name='login_farmer'),
    path('farmer/profile/', views.farmer_profile, name='farmer_profile'),
    path('farmer/dashboard/', views.farmer_dashboard_data, name='farmer_dashboard_data'),
    path('farmer/listings/', views.farmer_listings, name='farmer_listings'),
    path('farmer/reservations/', views.farmer_reservations, name='farmer_reservations'),
    path('farmer/urgent-sales/', views.urgent_sales, name='farmer_urgent_sales'),
    path('farmer/<int:farmer_id>/listings/', views.public_farmer_listings, name='public_farmer_listings'),

    # Buyer Marketplace APIs
    path('search/', views.search_products, name='search_products'),
    path('products/', views.get_all_products, name='get_all_products'),
    path('products/<int:listing_id>/', views.get_product_details, name='get_product_details'),
]
