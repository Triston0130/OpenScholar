#!/usr/bin/env python3
# database_setup.py - Database initialization and migration script

"""
Database setup and migration script for OpenScholar
Run this script to initialize the database and create tables
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import initialize_database, create_tables, check_database_health, db_manager
from app.database.models import User, Collection, Paper, Tag
from app.database.services import UserService, CollectionService, TagService
from app.logging import setup_logging, get_logger

def setup_database(database_url: str = None, echo: bool = False):
    """Initialize database and create tables"""
    logger = get_logger("database_setup")
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        initialize_database(database_url, echo)
        
        # Create tables
        logger.info("Creating database tables...")
        create_tables()
        
        # Check health
        health = check_database_health()
        if health["status"] == "healthy":
            logger.info("✅ Database setup completed successfully!")
            return True
        else:
            logger.error(f"❌ Database health check failed: {health.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

def create_default_data():
    """Create default system data"""
    logger = get_logger("database_setup")
    
    try:
        from app.database import get_session
        
        with get_session() as session:
            # Create system tags
            system_tags = [
                {"name": "external", "category": "source", "description": "Papers added from external sources"},
                {"name": "favorite", "category": "status", "description": "Favorite papers"},
                {"name": "to-read", "category": "status", "description": "Papers to read later"},
                {"name": "reading", "category": "status", "description": "Currently reading"},
                {"name": "completed", "category": "status", "description": "Finished reading"},
                {"name": "important", "category": "priority", "description": "Important papers"},
                {"name": "research", "category": "type", "description": "Research papers"},
                {"name": "review", "category": "type", "description": "Review papers"},
                {"name": "meta-analysis", "category": "type", "description": "Meta-analysis papers"},
            ]
            
            for tag_data in system_tags:
                existing_tag = session.query(Tag).filter(
                    Tag.name == tag_data["name"],
                    Tag.is_system_tag == True
                ).first()
                
                if not existing_tag:
                    tag = Tag(
                        name=tag_data["name"],
                        category=tag_data["category"],
                        description=tag_data.get("description"),
                        is_system_tag=True,
                        user_id=None
                    )
                    session.add(tag)
            
            session.commit()
            logger.info("✅ Default system data created successfully!")
            
    except Exception as e:
        logger.error(f"❌ Failed to create default data: {e}")

def migrate_from_localstorage():
    """Migration helper for moving from localStorage to database"""
    logger = get_logger("database_setup")
    
    logger.info("📝 LocalStorage migration guide:")
    print("""
    To migrate your existing data from localStorage to the database:
    
    1. Open your browser's developer tools
    2. Go to Application/Storage tab
    3. Find localStorage for your OpenScholar domain
    4. Export the following keys:
       - openscholar_collections
       - openscholar_settings
       
    5. Use the migration API endpoint:
       POST /api/migrate-localstorage
       {
         "collections": <exported_collections_data>,
         "settings": <exported_settings_data>
       }
    
    The API will automatically convert your localStorage data to the new database format.
    """)

def reset_database():
    """Reset database (drop and recreate all tables)"""
    logger = get_logger("database_setup")
    
    try:
        logger.warning("⚠️  Resetting database - all data will be lost!")
        
        # Drop tables
        db_manager.drop_tables()
        logger.info("Database tables dropped")
        
        # Recreate tables
        create_tables()
        logger.info("Database tables recreated")
        
        # Create default data
        create_default_data()
        
        logger.info("✅ Database reset completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
        return False

def main():
    """Main command line interface"""
    parser = argparse.ArgumentParser(description="OpenScholar Database Setup")
    parser.add_argument(
        "command",
        choices=["setup", "reset", "health", "migrate-guide"],
        help="Command to execute"
    )
    parser.add_argument(
        "--database-url",
        help="Database URL (overrides environment variable)"
    )
    parser.add_argument(
        "--echo",
        action="store_true",
        help="Enable SQL query logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging("database_setup", "INFO")
    logger = get_logger("database_setup")
    
    logger.info(f"🗄️  OpenScholar Database Setup - Command: {args.command}")
    
    if args.command == "setup":
        success = setup_database(args.database_url, args.echo)
        if success:
            create_default_data()
            print("\n✅ Database setup completed!")
            print("You can now start the OpenScholar API server.")
        else:
            print("\n❌ Database setup failed!")
            sys.exit(1)
    
    elif args.command == "reset":
        confirm = input("⚠️  This will delete ALL data. Type 'CONFIRM' to proceed: ")
        if confirm == "CONFIRM":
            initialize_database(args.database_url, args.echo)
            success = reset_database()
            if not success:
                sys.exit(1)
        else:
            print("Reset cancelled.")
    
    elif args.command == "health":
        if args.database_url:
            initialize_database(args.database_url, args.echo)
        
        health = check_database_health()
        print(f"Database Status: {health['status']}")
        
        if health['status'] == 'healthy':
            print(f"Engine: {health.get('engine', 'Unknown')}")
            print(f"Connection test: {health.get('connection_test', 'Unknown')}")
        else:
            print(f"Error: {health.get('error', 'Unknown error')}")
            sys.exit(1)
    
    elif args.command == "migrate-guide":
        migrate_from_localstorage()

if __name__ == "__main__":
    main()
