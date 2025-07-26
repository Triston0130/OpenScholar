# app/database/connection.py
"""
Database connection and session management for OpenScholar
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self, database_url: str = None, echo: bool = False):
        """Initialize database connection"""
        if self._initialized:
            return
        
        # Get database URL from environment or use SQLite fallback
        if not database_url:
            database_url = os.getenv(
                "DATABASE_URL", 
                "sqlite:///./openscholar.db"
            )
        
        # Handle PostgreSQL URLs from some hosting services
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # Create engine with appropriate settings
        if database_url.startswith("sqlite"):
            # SQLite settings
            self.engine = create_engine(
                database_url,
                echo=echo,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                }
            )
            # Enable foreign keys for SQLite
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                if 'sqlite' in str(dbapi_connection):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
        else:
            # PostgreSQL settings
            self.engine = create_engine(
                database_url,
                echo=echo,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._initialized = True
        logger.info(f"Database initialized with URL: {database_url.split('@')[0]}@...")
    
    def create_tables(self):
        """Create all database tables"""
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup"""
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get a database session (manual management required)"""
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        
        return self.SessionLocal()
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions
def initialize_database(database_url: str = None, echo: bool = False):
    """Initialize the global database manager"""
    db_manager.initialize(database_url, echo)

def create_tables():
    """Create all database tables"""
    db_manager.create_tables()

def get_session() -> Generator[Session, None, None]:
    """Get a database session context manager"""
    return db_manager.get_session()

def get_db_session() -> Session:
    """Get a database session for dependency injection"""
    return db_manager.get_session_sync()

# Database dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to get database session"""
    with db_manager.get_session() as session:
        yield session

# Health check function
def check_database_health() -> dict:
    """Check database connection health"""
    try:
        if not db_manager._initialized:
            return {
                "status": "unhealthy",
                "error": "Database not initialized"
            }
        
        with db_manager.get_session() as session:
            # Simple query to test connection
            result = session.execute("SELECT 1").scalar()
            
            return {
                "status": "healthy",
                "engine": str(db_manager.engine.url).split('@')[0] + '@...',
                "connection_test": "passed"
            }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
