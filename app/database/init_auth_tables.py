"""Initialize authentication tables in the database"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from app.database.models import Base
from app.database.models import User, UserSession, SearchHistory, Collection, APIUsage
from app.database.connection import get_database_url

def create_auth_tables():
    """Create all authentication-related tables"""
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    # Create all tables defined in the models
    Base.metadata.create_all(bind=engine, tables=[
        User.__table__,
        UserSession.__table__,
        SearchHistory.__table__,
        Collection.__table__,
        APIUsage.__table__
    ])
    
    print("Authentication tables created successfully!")
    print("Tables created:")
    print("- users")
    print("- user_sessions") 
    print("- search_history")
    print("- collections")
    print("- api_usage")

if __name__ == "__main__":
    create_auth_tables()