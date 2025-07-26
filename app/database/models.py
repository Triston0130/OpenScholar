# app/database/models.py
"""
Database models for OpenScholar
Replaces localStorage with proper PostgreSQL backend
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table,
    JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

# Association tables for many-to-many relationships
collection_papers = Table(
    'collection_papers',
    Base.metadata,
    Column('collection_id', UUID(as_uuid=True), ForeignKey('collections.id'), primary_key=True),
    Column('paper_id', UUID(as_uuid=True), ForeignKey('papers.id'), primary_key=True),
    Column('added_at', DateTime, default=datetime.utcnow),
    Column('notes', Text),
    Column('custom_tags', JSON),  # User-specific tags for this paper in this collection
)

paper_tags = Table(
    'paper_tags',
    Base.metadata,
    Column('paper_id', UUID(as_uuid=True), ForeignKey('papers.id'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id'), primary_key=True),
)

class User(Base):
    """User model for authentication and personalization"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255))  # Renamed from 'name'
    institution = Column(String(255))
    research_interests = Column(JSON)
    role = Column(String(50), default='researcher')  # student, researcher, educator, admin
    avatar_url = Column(String(500))
    
    # Authentication
    password_hash = Column(String(255), nullable=False)  # Now required
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Renamed from email_verified
    verification_token = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)  # Renamed from last_login_at
    
    # Settings
    preferences = Column(JSON)  # User preferences and settings
    
    # Relationships
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    email_settings = relationship("UserEmailSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notification_preferences = relationship("UserNotificationPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.full_name}')>"

class Collection(Base):
    """Collection model for organizing papers"""
    __tablename__ = 'collections'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    color = Column(String(7))  # Hex color code
    icon = Column(String(50))  # Icon name or emoji
    
    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Sharing and collaboration
    is_public = Column(Boolean, default=False)
    is_shared = Column(Boolean, default=False)
    share_token = Column(String(32), unique=True)  # For sharing collections
    
    # Organization
    parent_id = Column(UUID(as_uuid=True), ForeignKey('collections.id'))  # For nested collections
    sort_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Metadata
    paper_count = Column(Integer, default=0)  # Cached count for performance
    tags = Column(JSON)  # Collection-level tags
    extra_metadata = Column(JSON)  # Additional metadata
    
    # Relationships
    user = relationship("User", back_populates="collections")
    papers = relationship("Paper", secondary=collection_papers, back_populates="collections")
    subcollections = relationship("Collection", remote_side=[id])
    
    # Indexes
    __table_args__ = (
        Index('idx_collection_user_name', 'user_id', 'name'),
        Index('idx_collection_public', 'is_public'),
        Index('idx_collection_parent', 'parent_id'),
    )
    
    def __repr__(self):
        return f"<Collection(name='{self.name}', user_id='{self.user_id}')>"

class Paper(Base):
    """Paper model for storing academic papers"""
    __tablename__ = 'papers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core paper information
    title = Column(String(1000), nullable=False)
    authors = Column(JSON, nullable=False)  # List of author names
    abstract = Column(Text)
    year = Column(String(4))
    journal = Column(String(500))
    venue = Column(String(500))  # Conference or journal venue
    
    # Identifiers
    doi = Column(String(255), index=True)
    arxiv_id = Column(String(50))
    pubmed_id = Column(String(50))
    isbn = Column(String(20))
    
    # URLs and access
    url = Column(String(1000))
    pdf_url = Column(String(1000))
    full_text_url = Column(String(1000))
    
    # Metrics and metadata
    citation_count = Column(Integer)
    influential_citation_count = Column(Integer)
    source = Column(String(100), nullable=False)  # Which API/source this came from
    
    # Content analysis
    keywords = Column(JSON)  # List of extracted keywords
    subjects = Column(JSON)  # Subject classifications
    language = Column(String(10), default='en')
    
    # Publication details
    publication_type = Column(String(50))  # journal-article, conference-paper, etc.
    study_type = Column(String(50))  # experimental, review, meta-analysis, etc.
    page_start = Column(String(20))
    page_end = Column(String(20))
    volume = Column(String(20))
    issue = Column(String(20))
    
    # Quality indicators
    is_open_access = Column(Boolean)
    peer_reviewed = Column(Boolean)
    retracted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime)
    
    # Additional metadata
    extra_metadata = Column(JSON)  # Store additional fields from different APIs
    
    # Relationships
    collections = relationship("Collection", secondary=collection_papers, back_populates="papers")
    tags = relationship("Tag", secondary=paper_tags, back_populates="papers")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_paper_title', 'title'),
        Index('idx_paper_doi', 'doi'),
        Index('idx_paper_year', 'year'),
        Index('idx_paper_source', 'source'),
        Index('idx_paper_created', 'created_at'),
        UniqueConstraint('doi', name='uq_paper_doi'),
    )
    
    def __repr__(self):
        return f"<Paper(title='{self.title[:50]}...', year='{self.year}')>"

class Tag(Base):
    """Tag model for categorizing papers"""
    __tablename__ = 'tags'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    color = Column(String(7))  # Hex color code
    
    # Organization
    category = Column(String(50))  # subject, methodology, status, etc.
    parent_id = Column(UUID(as_uuid=True), ForeignKey('tags.id'))  # For hierarchical tags
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    
    # Ownership (global tags vs user tags)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))  # None for global tags
    is_system_tag = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    papers = relationship("Paper", secondary=paper_tags, back_populates="tags")
    user = relationship("User")
    subtags = relationship("Tag", remote_side=[id])
    
    # Indexes
    __table_args__ = (
        Index('idx_tag_name', 'name'),
        Index('idx_tag_category', 'category'),
        Index('idx_tag_user', 'user_id'),
        UniqueConstraint('name', 'user_id', name='uq_tag_name_user'),
    )
    
    def __repr__(self):
        return f"<Tag(name='{self.name}', category='{self.category}')>"

class SearchHistory(Base):
    """Search history for analytics and user experience"""
    __tablename__ = 'search_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Search details
    query = Column(String(1000), nullable=False)
    filters = Column(JSON)  # Search filters applied
    results_count = Column(Integer)
    sources_queried = Column(JSON)  # List of APIs queried
    
    # Performance metrics
    search_duration_ms = Column(Integer)
    cache_hit = Column(Boolean, default=False)
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    session_id = Column(String(100))  # For tracking search sessions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional context
    user_agent = Column(String(500))
    ip_address = Column(String(45))  # IPv6 compatible
    
    # Relationships
    user = relationship("User", back_populates="search_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_search_user_created', 'user_id', 'created_at'),
        Index('idx_search_query', 'query'),
        Index('idx_search_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SearchHistory(query='{self.query[:30]}...', user_id='{self.user_id}')>"

class APIUsage(Base):
    """Track API usage for monitoring and rate limiting"""
    __tablename__ = 'api_usage'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # API details
    api_name = Column(String(50), nullable=False)
    endpoint = Column(String(200))
    method = Column(String(10))
    
    # Request details
    query_params = Column(JSON)
    response_status = Column(Integer)
    response_time_ms = Column(Integer)
    
    # Results
    results_returned = Column(Integer)
    cache_hit = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Rate limiting
    rate_limit_remaining = Column(Integer)
    rate_limit_reset = Column(DateTime)
    
    # Context
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    search_history_id = Column(UUID(as_uuid=True), ForeignKey('search_history.id'))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    search_history = relationship("SearchHistory")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_usage_api_created', 'api_name', 'created_at'),
        Index('idx_api_usage_user_created', 'user_id', 'created_at'),
        Index('idx_api_usage_status', 'response_status'),
    )
    
    def __repr__(self):
        return f"<APIUsage(api_name='{self.api_name}', status='{self.response_status}')>"

class UserSession(Base):
    """User session management"""
    __tablename__ = 'user_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Session details
    access_token = Column(String(500), unique=True, nullable=False)  # JWT tokens are longer
    refresh_token = Column(String(500), unique=True)
    
    # Session metadata
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    device_info = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Session state
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_session_access_token', 'access_token'),
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', active='{self.is_active}')>"
