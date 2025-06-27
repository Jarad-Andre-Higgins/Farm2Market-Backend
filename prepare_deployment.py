#!/usr/bin/env python3
"""
Prepare Farm2Market for Railway deployment
This script copies the Frontend folder and prepares all files for deployment
"""

import os
import shutil
import sys
from pathlib import Path

def prepare_deployment():
    """Prepare the project for Railway deployment"""
    
    print("🚀 Preparing Farm2Market for Railway deployment...")
    
    # Get current directory (should be AGRIPORT)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent  # farm2market directory
    frontend_source = project_root / "Frontend"
    frontend_dest = current_dir / "Frontend"
    
    print(f"📁 Current directory: {current_dir}")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Frontend source: {frontend_source}")
    print(f"📁 Frontend destination: {frontend_dest}")
    
    # Check if Frontend source exists
    if not frontend_source.exists():
        print(f"❌ Frontend folder not found at: {frontend_source}")
        return False
    
    # Remove existing Frontend folder in AGRIPORT if it exists
    if frontend_dest.exists():
        print("🗑️  Removing existing Frontend folder...")
        shutil.rmtree(frontend_dest)
    
    # Copy Frontend folder to AGRIPORT
    print("📋 Copying Frontend folder...")
    shutil.copytree(frontend_source, frontend_dest)
    
    # Create templates directory structure for Django
    templates_dir = current_dir / "farm2market_backend" / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Create symbolic link or copy key HTML files to templates
    key_files = [
        "index.html",
        "Admin/admin_login.html",
        "Farmer/loginfarmer.html",
        "Buyer/loginbuyer.html",
        "Farmer/signupfarmer.html",
        "Buyer/signupbuyer.html",
        "Buyer/marketplace.html",
        "Admin/admin_dashboard.html",
        "Farmer/farmer dashboard.html",
        "Buyer/buyerdashboard.html"
    ]
    
    print("📄 Setting up template files...")
    for file_path in key_files:
        source_file = frontend_dest / file_path
        if source_file.exists():
            # Create directory structure in templates
            template_file = templates_dir / file_path
            template_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_file, template_file)
            print(f"   ✅ Copied: {file_path}")
        else:
            print(f"   ⚠️  Not found: {file_path}")
    
    # Update static files configuration
    print("⚙️  Checking configuration files...")
    
    # Check if all required files exist
    required_files = [
        "requirements.txt",
        "Procfile",
        "railway.json",
        "farm2market_backend/settings_production.py"
    ]
    
    for file_name in required_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"   ✅ Found: {file_name}")
        else:
            print(f"   ❌ Missing: {file_name}")
    
    print("\n🎉 Deployment preparation complete!")
    print("\n📋 Next steps:")
    print("1. Push your AGRIPORT folder to GitHub")
    print("2. Deploy on Railway.app")
    print("3. Add MySQL database service")
    print("4. Set environment variables")
    print("5. Your app will be live!")
    
    return True

if __name__ == "__main__":
    success = prepare_deployment()
    if not success:
        sys.exit(1)
