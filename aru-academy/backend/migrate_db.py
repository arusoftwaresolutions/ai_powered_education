#!/usr/bin/env python3
"""
Database Migration Script for ARU Academy
This script handles database migrations during deployment
"""

import os
import sys
from flask import Flask
from sqlalchemy import text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.base import db, migrate
from config.settings import Config

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    migrate.init_app(app, db)
    
    return app

def check_database_connection():
    """Check if database connection is working"""
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def get_existing_tables():
    """Get list of existing tables"""
    try:
        inspector = inspect(db.engine)
        return inspector.get_table_names()
    except Exception as e:
        print(f"❌ Error getting table list: {e}")
        return []

def run_migrations():
    """Run database migrations"""
    print("🔄 Running database migrations...")
    
    try:
        from flask_migrate import upgrade, init, migrate as migrate_cmd
        upgrade()
        print("✅ Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def create_tables_if_not_exist():
    """Create tables if they don't exist"""
    print("🏗️  Creating tables if they don't exist...")
    
    try:
        db.create_all()
        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def seed_if_empty():
    """Seed database if it's empty"""
    print("🌱 Checking if database needs seeding...")
    
    try:
        # Check if we have any users
        from models.user import User
        user_count = User.query.count()
        
        if user_count == 0:
            print("📊 Database is empty, seeding with initial data...")
            from seed.seed import seed_database
            seed_database()
            print("✅ Database seeded successfully!")
        else:
            print(f"✅ Database already has {user_count} users, skipping seed.")
        
        return True
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        return False

def force_seed_database():
    """Force seed the database (for production deployment)"""
    print("🌱 Force seeding database with fresh data...")
    
    try:
        from seed.seed import seed_database
        seed_database()
        print("✅ Database force seeded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error force seeding database: {e}")
        return False

def drop_all_tables():
    """Drop all existing tables"""
    print("🗑️  Dropping all existing tables...")
    
    try:
        # Get all table names
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        
        if not table_names:
            print("✅ No tables found to drop.")
            return True
        
        print(f"Found {len(table_names)} tables to drop:")
        for table in table_names:
            print(f"  - {table}")
        
        # Drop all tables
        with db.engine.connect() as conn:
            # Disable foreign key checks temporarily
            if 'mysql' in str(db.engine.url):
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            
            # Drop all tables
            for table in reversed(table_names):
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
                    print(f"  ✅ Dropped table: {table}")
                except Exception as e:
                    print(f"  ⚠️  Warning: Could not drop table {table}: {e}")
            
            # Re-enable foreign key checks
            if 'mysql' in str(db.engine.url):
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            
            conn.commit()
        
        print("✅ All tables dropped successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 ARU Academy Database Migration")
    print("=" * 40)
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Check database connection
            print("🔌 Testing database connection...")
            if not check_database_connection():
                sys.exit(1)
            print("✅ Database connection successful!")
            
            # Step 2: Drop all existing tables
            if not drop_all_tables():
                sys.exit(1)
            
            # Step 3: Create fresh tables
            print("🏗️  Creating fresh tables...")
            if not create_tables_if_not_exist():
                sys.exit(1)
            
            # Step 4: Run migrations
            if not run_migrations():
                sys.exit(1)
            
            # Step 5: Force seed database (for production)
            if not force_seed_database():
                sys.exit(1)
            
            print("\n🎉 Database migration completed successfully!")
            print("Your ARU Academy database is ready to use.")
            
        except Exception as e:
            print(f"\n❌ Database migration failed: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
