"""
Simple script to serve frontend files through Django
"""
import os
import shutil

def setup_frontend_serving():
    """Copy frontend files to Django static directory"""
    
    # Create templates directory
    templates_dir = 'templates'
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Frontend files to copy
    frontend_files = [
        '../Frontend/test-registration.html',
        '../Frontend/Farmer/farmer dashboard.html',
        '../Frontend/Farmer/loginfarmer.html'
    ]
    
    for file_path in frontend_files:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            destination = os.path.join(templates_dir, filename)
            shutil.copy2(file_path, destination)
            print(f"Copied {filename} to templates/")
        else:
            print(f"File not found: {file_path}")

if __name__ == '__main__':
    setup_frontend_serving()
