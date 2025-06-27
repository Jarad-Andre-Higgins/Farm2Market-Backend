#!/usr/bin/env python
"""
Setup default admin roles for Agriport system
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm2market_backend.settings')
django.setup()

from farm2market_backend.coreF2M.models import AdminRole

def create_default_roles():
    """Create default admin roles with permissions"""
    
    roles_data = [
        {
            'name': 'super_admin',
            'display_name': 'Super Administrator',
            'description': 'Full system access with all permissions',
            'permissions': {
                'user_management': True,
                'admin_management': True,
                'transaction_management': True,
                'content_moderation': True,
                'analytics_access': True,
                'system_configuration': True,
                'role_assignment': True,
                'audit_logs': True,
                'global_search': True,
                'delete_users': True,
                'approve_farmers': True,
                'manage_categories': True,
                'send_notifications': True
            }
        },
        {
            'name': 'user_manager',
            'display_name': 'User Manager',
            'description': 'Manage farmers and buyers, approve registrations',
            'permissions': {
                'user_management': True,
                'admin_management': False,
                'transaction_management': False,
                'content_moderation': True,
                'analytics_access': True,
                'system_configuration': False,
                'role_assignment': False,
                'audit_logs': True,
                'global_search': True,
                'delete_users': False,
                'approve_farmers': True,
                'manage_categories': False,
                'send_notifications': True
            }
        },
        {
            'name': 'transaction_manager',
            'display_name': 'Transaction Manager',
            'description': 'Manage transactions, reservations, and financial data',
            'permissions': {
                'user_management': False,
                'admin_management': False,
                'transaction_management': True,
                'content_moderation': False,
                'analytics_access': True,
                'system_configuration': False,
                'role_assignment': False,
                'audit_logs': True,
                'global_search': True,
                'delete_users': False,
                'approve_farmers': False,
                'manage_categories': False,
                'send_notifications': True
            }
        },
        {
            'name': 'content_moderator',
            'display_name': 'Content Moderator',
            'description': 'Moderate listings, reviews, and user content',
            'permissions': {
                'user_management': False,
                'admin_management': False,
                'transaction_management': False,
                'content_moderation': True,
                'analytics_access': False,
                'system_configuration': False,
                'role_assignment': False,
                'audit_logs': False,
                'global_search': True,
                'delete_users': False,
                'approve_farmers': False,
                'manage_categories': True,
                'send_notifications': False
            }
        },
        {
            'name': 'analytics_viewer',
            'display_name': 'Analytics Viewer',
            'description': 'View system analytics and reports',
            'permissions': {
                'user_management': False,
                'admin_management': False,
                'transaction_management': False,
                'content_moderation': False,
                'analytics_access': True,
                'system_configuration': False,
                'role_assignment': False,
                'audit_logs': True,
                'global_search': True,
                'delete_users': False,
                'approve_farmers': False,
                'manage_categories': False,
                'send_notifications': False
            }
        },
        {
            'name': 'support_agent',
            'display_name': 'Support Agent',
            'description': 'Handle user support and basic system operations',
            'permissions': {
                'user_management': False,
                'admin_management': False,
                'transaction_management': False,
                'content_moderation': False,
                'analytics_access': False,
                'system_configuration': False,
                'role_assignment': False,
                'audit_logs': False,
                'global_search': True,
                'delete_users': False,
                'approve_farmers': False,
                'manage_categories': False,
                'send_notifications': True
            }
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for role_data in roles_data:
        role, created = AdminRole.objects.get_or_create(
            name=role_data['name'],
            defaults={
                'display_name': role_data['display_name'],
                'description': role_data['description'],
                'permissions': role_data['permissions'],
                'is_active': True
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ Created role: {role.display_name}")
        else:
            # Update existing role
            role.display_name = role_data['display_name']
            role.description = role_data['description']
            role.permissions = role_data['permissions']
            role.is_active = True
            role.save()
            updated_count += 1
            print(f"🔄 Updated role: {role.display_name}")
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} roles")
    print(f"   Updated: {updated_count} roles")
    print(f"   Total: {created_count + updated_count} roles")
    
    return created_count + updated_count

if __name__ == '__main__':
    print("🚀 Setting up default admin roles for Agriport...")
    print("=" * 60)
    
    try:
        total_roles = create_default_roles()
        
        print("\n🎉 Admin roles setup completed successfully!")
        print(f"   {total_roles} roles are now available in the system")
        
        # List all roles
        print("\n📋 Available Admin Roles:")
        roles = AdminRole.objects.filter(is_active=True).order_by('name')
        for role in roles:
            print(f"   • {role.display_name} ({role.name})")
            print(f"     {role.description}")
            print(f"     Permissions: {len([k for k, v in role.permissions.items() if v])} enabled")
            print()
        
    except Exception as e:
        print(f"❌ Error setting up admin roles: {e}")
        import traceback
        traceback.print_exc()
