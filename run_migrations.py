"""
Best Practice Migration Manager
Automatically runs SQL migrations in order before initializing SQLAlchemy models
"""

import os
import sys
from pathlib import Path
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.database_init import engine
from app.models.database import Base


def run_sql_migrations():
    """Run all SQL migration files in order"""
    migrations_dir = Path(__file__).parent / "migrations"
    
    if not migrations_dir.exists():
        print("⚠️  Migrations directory not found")
        return
    
    # Get all SQL files sorted by name
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("ℹ️  No migration files found")
        return
    
    print(f"\n📂 Found {len(migration_files)} migration files")
    
    with engine.begin() as conn:
        for migration_file in migration_files:
            print(f"   ▶ Running: {migration_file.name}")
            
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Split by semicolon and execute each statement
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for statement in statements:
                    conn.execute(text(statement))
                
                print(f"     ✅ Completed: {migration_file.name}")
            
            except Exception as e:
                print(f"     ❌ Error in {migration_file.name}: {str(e)}")
                raise


def init_database():
    """Initialize database tables from SQLAlchemy models"""
    print("\n📋 Creating tables from models...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created/updated from models")


def main():
    """Main migration runner"""
    print("=" * 60)
    print("Rice Detection Database Migration Manager")
    print("=" * 60)
    
    try:
        # Step 1: Run SQL migrations
        print("\n[Step 1/2] Running SQL migrations...")
        run_sql_migrations()
        
        # Step 2: Initialize models
        print("\n[Step 2/2] Initializing SQLAlchemy models...")
        init_database()
        
        print("\n" + "=" * 60)
        print("✨ All migrations completed successfully!")
        print("=" * 60)
        
        return True
    
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
