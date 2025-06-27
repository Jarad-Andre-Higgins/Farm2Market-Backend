"""
URL configuration for farm2market_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse, FileResponse
from farm2market_backend.coreF2M.views import (
    home_view, admin_login_view, farmer_login_view, buyer_login_view,
    farmer_signup_view, buyer_signup_view, marketplace_view,
    admin_dashboard_view, farmer_dashboard_view, buyer_dashboard_view
)
import os
import mimetypes

def landing_page_view(request):
    """Serve the main landing page with navigation"""
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌾 Farm2Market - Agricultural Marketplace</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c5530; text-align: center; }
            .section { margin: 20px 0; }
            .links { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
            .link-card { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; }
            .link-card a { text-decoration: none; color: #2c5530; font-weight: bold; }
            .link-card a:hover { color: #28a745; }
            .status { background: #d4edda; padding: 10px; border-radius: 5px; color: #155724; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌾 Farm2Market - Agricultural Marketplace</h1>
            <div class="status">
                <strong>✅ System Status:</strong> Fully Operational & Ready for Production!
            </div>

            <div class="section">
                <h3>🚀 User Portals:</h3>
                <div class="links">
                    <div class="link-card">
                        <a href="/admin/">🔧 Admin Panel</a><br>
                        <small>Complete system management</small>
                    </div>
                    <div class="link-card">
                        <a href="/farmer/login/">🚜 Farmer Portal</a><br>
                        <small>Product listing & management</small>
                    </div>
                    <div class="link-card">
                        <a href="/buyer/login/">🛒 Buyer Portal</a><br>
                        <small>Marketplace & reservations</small>
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>📊 API Endpoints:</h3>
                <div class="links">
                    <div class="link-card">
                        <a href="/api/">📡 API Root</a><br>
                        <small>All available endpoints</small>
                    </div>
                    <div class="link-card">
                        <a href="/api/products/">🌱 Products API</a><br>
                        <small>Browse all products</small>
                    </div>
                    <div class="link-card">
                        <a href="/api/search/">🔍 Search API</a><br>
                        <small>Search functionality</small>
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>🎯 Default Credentials:</h3>
                <p><strong>Admin:</strong> admin@farm2market.com / admin123</p>
                <p><strong>Test Accounts:</strong> Create via registration forms</p>
            </div>
        </div>
    </body>
    </html>
    """)

def serve_frontend_file(request, filename):
    """Serve frontend files"""
    frontend_path = os.path.join(settings.BASE_DIR, '..', 'Frontend')

    # Define file mappings
    file_mappings = {
        'test-registration.html': os.path.join(frontend_path, 'test-registration.html'),
        'farmer-dashboard.html': os.path.join(frontend_path, 'Farmer', 'farmer dashboard.html'),
        'loginfarmer.html': os.path.join(frontend_path, 'Farmer', 'loginfarmer.html'),
        'buyer-dashboard.html': os.path.join(frontend_path, 'Buyer', 'buyerdashboard.html'),
        'buyer-signup.html': os.path.join(frontend_path, 'Buyer', 'signupbuyer.html'),
        'buyer-login.html': os.path.join(frontend_path, 'Buyer', 'loginbuyer.html'),
        'buyer-join.html': os.path.join(frontend_path, 'Buyer', 'joinbuyer.html'),
    }

    if filename not in file_mappings:
        return HttpResponse("File not found", status=404)

    file_path = file_mappings[filename]

    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='text/html')
    else:
        return HttpResponse(f"File not found: {file_path}", status=404)

def serve_static_file(request, file_path):
    """Serve static files (CSS, JS, images) from Frontend directory"""
    frontend_path = os.path.join(settings.BASE_DIR, '..', 'Frontend')
    full_path = os.path.join(frontend_path, file_path)

    if os.path.exists(full_path) and os.path.isfile(full_path):
        # Determine content type
        content_type, _ = mimetypes.guess_type(full_path)
        if content_type is None:
            content_type = 'application/octet-stream'

        return FileResponse(open(full_path, 'rb'), content_type=content_type)
    else:
        return HttpResponse(f"Static file not found: {file_path}", status=404)

urlpatterns = [
    # Main pages
    path('', landing_page_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('farm2market_backend.coreF2M.urls')),

    # Frontend Portal Routes
    path('admin/login/', admin_login_view, name='admin_login'),
    path('farmer/login/', farmer_login_view, name='farmer_login'),
    path('farmer/signup/', farmer_signup_view, name='farmer_signup'),
    path('farmer/dashboard/', farmer_dashboard_view, name='farmer_dashboard'),
    path('buyer/login/', buyer_login_view, name='buyer_login'),
    path('buyer/signup/', buyer_signup_view, name='buyer_signup'),
    path('buyer/dashboard/', buyer_dashboard_view, name='buyer_dashboard'),
    path('marketplace/', marketplace_view, name='marketplace'),

    # Legacy routes for backward compatibility
    path('buyer-dashboard.html', serve_frontend_file, {'filename': 'buyer-dashboard.html'}),
    path('buyer-signup.html', serve_frontend_file, {'filename': 'buyer-signup.html'}),
    path('buyer-login.html', serve_frontend_file, {'filename': 'buyer-login.html'}),
    path('buyer-join.html', serve_frontend_file, {'filename': 'buyer-join.html'}),
    path('farmer-dashboard.html', serve_frontend_file, {'filename': 'farmer-dashboard.html'}),
    path('loginfarmer.html', serve_frontend_file, {'filename': 'loginfarmer.html'}),
    path('test-registration.html', serve_frontend_file, {'filename': 'test-registration.html'}),

    # Serve static files from Frontend directory
    re_path(r'^Frontend/(?P<file_path>.*)$', serve_static_file),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
