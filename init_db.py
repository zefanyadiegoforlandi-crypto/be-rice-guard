#!/usr/bin/env python
"""
Database initialization script untuk Rice Detection Backend
Run ini setelah MySQL database sudah dibuat
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("=" * 60)
    print("Rice Detection Database Initialization")
    print("=" * 60)
    
    # Check if .env exists
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("\n⚠️  WARNING: .env file not found!")
        print(f"   Expected at: {env_path}")
        print("\n   Please create .env file first:")
        print("   1. Copy .env.example to .env")
        print("   2. Update with your MySQL credentials")
        return False
    
    print("\n✓ .env file found")
    
    # Try to import and initialize database
    try:
        print("\n📦 Importing database modules...")
        from app.models.database_init import init_db
        from app.config import SQLALCHEMY_DATABASE_URL
        
        print(f"✓ Database URL: {SQLALCHEMY_DATABASE_URL}")
        
        print("\n🔄 Creating tables...")
        init_db()
        
        print("\n✅ Database initialized successfully!")
        print("\n📋 Tables created:")
        print("   • users - User accounts")
        print("   • detections - Scan history")
        print("   • image_metadata - Image info")
        
        print("\n📁 Image storage location: backend/app/uploads/")
        print("\n✨ You're all set! Start the server with:")
        print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
        
        return True
        
    except ModuleNotFoundError as e:
        print(f"\n❌ ERROR: Missing module: {e}")
        print("   Please install requirements first:")
        print("   pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify MySQL is running")
        print("  2. Check .env credentials")
        print("  3. Ensure database exists: CREATE DATABASE rice_detection_db;")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
