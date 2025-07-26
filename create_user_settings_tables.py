#!/usr/bin/env python3
"""
Create user settings tables in the database
"""

from app.database import db_manager, Base
from app.database.user_settings import UserEmailSettings, UserNotificationPreferences
from app.database.sharing_models import CollectionShare, FolderShare, Folder, PDFAnnotation, AnnotationReply, PDFCache

if __name__ == "__main__":
    print("Creating user settings and sharing tables...")
    
    # Initialize database
    db_manager.initialize()
    
    # Create all tables
    Base.metadata.create_all(bind=db_manager.engine)
    
    print("Tables created successfully!")
    print("You can now use the email settings and sharing features.")