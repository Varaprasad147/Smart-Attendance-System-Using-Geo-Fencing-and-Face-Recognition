#!/usr/bin/env python3
"""
Setup script for the Geofenced Intelligent Attendance System.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        'media',
        'media/faces',
        'static',
        'logs',
        'templates',
        'templates/users',
        'templates/super',
        'templates/admin',
        'templates/student'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def create_env_file():
    """Create .env file from template."""
    if not os.path.exists('.env'):
        if os.path.exists('env.example'):
            shutil.copy('env.example', '.env')
            print("📝 Created .env file from template")
            print("⚠️  Please edit .env file with your actual configuration values")
        else:
            print("⚠️  env.example not found, please create .env file manually")
    else:
        print("📝 .env file already exists")

def install_dependencies():
    """Install Python dependencies."""
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    return True

def setup_database():
    """Setup database and run migrations."""
    print("\n🗄️  Setting up database...")
    
    # Check if MySQL is running (basic check)
    try:
        result = subprocess.run("mysql --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MySQL is available")
        else:
            print("⚠️  MySQL not found or not accessible")
            print("Please ensure MySQL is running and accessible")
    except FileNotFoundError:
        print("⚠️  MySQL command not found")
        print("Please install MySQL and ensure it's in your PATH")
    
    print("\n📋 Next steps:")
    print("1. Create MySQL database: CREATE DATABASE attendance_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print("2. Update .env file with your database credentials")
    print("3. Run: python manage.py makemigrations")
    print("4. Run: python manage.py migrate")
    print("5. Run: python manage.py seed_superadmin")

def main():
    """Main setup function."""
    print("🚀 Setting up Geofenced Intelligent Attendance System")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Setup database
    setup_database()
    
    print("\n🎉 Setup completed!")
    print("\n📚 For detailed setup instructions, see README.md")
    print("\n🔧 To start the system:")
    print("1. Start Redis: redis-server")
    print("2. Start Celery: celery -A attendance_system worker --loglevel=info")
    print("3. Start Face Service: cd face_service && uvicorn main:app --reload --port 8001")
    print("4. Start Django: python manage.py runserver")

if __name__ == "__main__":
    main()
