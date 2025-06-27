#!/usr/bin/env python
"""
Production deployment script for Farm2Market
"""
import os
import sys
import subprocess
import secrets

def generate_secret_key():
    """Generate a secure Django secret key"""
    return secrets.token_urlsafe(50)

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = '.env'
    env_example = '.env.example'
    
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            # Copy template and generate secret key
            with open(env_example, 'r') as f:
                content = f.read()
            
            # Replace placeholder with actual secret key
            secret_key = generate_secret_key()
            content = content.replace('your-super-secret-key-here-change-this-in-production', secret_key)
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Created {env_file} from template")
            print(f"🔑 Generated secure secret key")
            print(f"⚠️  Please edit {env_file} and update the database and email settings")
        else:
            print(f"❌ {env_example} not found")
            return False
    else:
        print(f"✅ {env_file} already exists")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    try:
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'farm2market_backend/requirements.txt'], check=True)
        
        # Install additional production dependencies
        production_deps = [
            'python-dotenv',  # For environment variables
            'gunicorn',       # WSGI server
            'redis',          # For caching
        ]
        
        for dep in production_deps:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def collect_static_files():
    """Collect static files for production"""
    try:
        print("📁 Collecting static files...")
        subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'], check=True)
        print("✅ Static files collected successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to collect static files: {e}")
        return False

def run_migrations():
    """Run database migrations"""
    try:
        print("🗄️  Running database migrations...")
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        print("✅ Migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run migrations: {e}")
        return False

def create_superuser():
    """Create superuser if it doesn't exist"""
    try:
        print("👤 Creating admin user...")
        subprocess.run([sys.executable, 'create_admin.py'], check=True)
        print("✅ Admin user ready")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create admin user: {e}")
        return False

def check_system_requirements():
    """Check if system requirements are met"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print("✅ Python version OK")
    
    # Check if MySQL is available
    try:
        import mysql.connector
        print("✅ MySQL connector available")
    except ImportError:
        print("❌ MySQL connector not available")
        return False
    
    return True

def main():
    """Main deployment function"""
    print("🚀 Farm2Market Production Deployment")
    print("=" * 50)
    
    # Check system requirements
    if not check_system_requirements():
        print("❌ System requirements not met")
        return False
    
    # Create environment file
    if not create_env_file():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Run migrations
    if not run_migrations():
        return False
    
    # Create superuser
    if not create_superuser():
        return False
    
    # Collect static files
    if not collect_static_files():
        return False
    
    print("\n" + "=" * 50)
    print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your actual database and email settings")
    print("2. Configure your web server (nginx/apache)")
    print("3. Set up SSL certificate for HTTPS")
    print("4. Configure firewall settings")
    print("5. Set up monitoring and backups")
    print("\n🌐 Access your application:")
    print("- Admin Panel: http://localhost:8000/admin/")
    print("- API: http://localhost:8000/api/")
    print("- Frontend: http://localhost:8000/")
    print("\n🔐 Admin Credentials:")
    print("- Email: admin@farm2market.com")
    print("- Username: admin")
    print("- Password: admin123")
    print("\n⚠️  Remember to change the admin password in production!")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
