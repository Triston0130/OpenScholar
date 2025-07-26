# app/database/sharing_models.py
"""
Database models for collection sharing and PDF annotations
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, 
    JSON, Index, UniqueConstraint, Float, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from .models import Base

class ShareRole(enum.Enum):
    """Roles for shared collections"""
    VIEWER = "viewer"          # Can view papers and annotations
    COMMENTER = "commenter"    # Can view and comment
    EDITOR = "editor"         # Can add/remove papers, edit metadata
    ADMIN = "admin"           # Full control including sharing

class CollectionShare(Base):
    """Model for sharing collections with other users"""
    __tablename__ = 'collection_shares'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey('collections.id'), nullable=False)
    
    # Who shared it and who it's shared with
    shared_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    shared_with_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))  # Null for link shares
    shared_with_email = Column(String(255))  # For inviting non-users
    
    # Permissions
    role = Column(Enum(ShareRole), default=ShareRole.VIEWER, nullable=False)
    can_reshare = Column(Boolean, default=False)
    
    # Share details
    share_link = Column(String(100), unique=True)  # For public link sharing
    expires_at = Column(DateTime)
    message = Column(Text)  # Optional message from sharer
    
    # Status
    accepted = Column(Boolean, default=False)
    accepted_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collection = relationship("Collection", foreign_keys=[collection_id])
    shared_by = relationship("User", foreign_keys=[shared_by_user_id])
    shared_with = relationship("User", foreign_keys=[shared_with_user_id])
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('collection_id', 'shared_with_user_id', name='uq_collection_user_share'),
        UniqueConstraint('collection_id', 'shared_with_email', name='uq_collection_email_share'),
        Index('idx_share_collection', 'collection_id'),
        Index('idx_share_user', 'shared_with_user_id'),
        Index('idx_share_link', 'share_link'),
    )

class FolderShare(Base):
    """Model for sharing specific folders within collections"""
    __tablename__ = 'folder_shares'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    folder_id = Column(UUID(as_uuid=True), ForeignKey('folders.id'), nullable=False)
    collection_id = Column(UUID(as_uuid=True), ForeignKey('collections.id'), nullable=False)
    
    # Similar structure to CollectionShare
    shared_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    shared_with_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    shared_with_email = Column(String(255))
    
    role = Column(Enum(ShareRole), default=ShareRole.VIEWER, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class Folder(Base):
    """Model for folders within collections"""
    __tablename__ = 'folders'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    collection_id = Column(UUID(as_uuid=True), ForeignKey('collections.id'), nullable=False)
    parent_folder_id = Column(UUID(as_uuid=True), ForeignKey('folders.id'))
    
    # Ownership
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Metadata
    color = Column(String(7))
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collection = relationship("Collection", foreign_keys=[collection_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    subfolders = relationship("Folder", remote_side=[id])
    shares = relationship("FolderShare", back_populates="folder", cascade="all, delete-orphan")

# Update FolderShare relationship
FolderShare.folder = relationship("Folder", back_populates="shares")

class PDFAnnotation(Base):
    """Model for PDF highlights and comments"""
    __tablename__ = 'pdf_annotations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey('papers.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    collection_id = Column(UUID(as_uuid=True), ForeignKey('collections.id'))  # Optional: which collection context
    
    # Annotation type
    annotation_type = Column(String(20), nullable=False)  # highlight, comment, note, bookmark
    color = Column(String(7), default='#FFFF00')  # Highlight color
    
    # Position in PDF
    page_number = Column(Integer, nullable=False)
    position_x = Column(Float)
    position_y = Column(Float)
    width = Column(Float)
    height = Column(Float)
    
    # Text selection
    selected_text = Column(Text)  # The highlighted text
    start_offset = Column(Integer)  # Character offset in page
    end_offset = Column(Integer)
    
    # Content
    comment = Column(Text)  # User's comment/note
    tags = Column(JSON)  # Tags for this annotation
    
    # Sharing
    is_private = Column(Boolean, default=True)
    shared_in_collection = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", foreign_keys=[paper_id])
    user = relationship("User", foreign_keys=[user_id])
    collection = relationship("Collection", foreign_keys=[collection_id])
    replies = relationship("AnnotationReply", back_populates="annotation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_annotation_paper_user', 'paper_id', 'user_id'),
        Index('idx_annotation_collection', 'collection_id'),
        Index('idx_annotation_type', 'annotation_type'),
    )

class AnnotationReply(Base):
    """Model for replies/discussions on annotations"""
    __tablename__ = 'annotation_replies'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    annotation_id = Column(UUID(as_uuid=True), ForeignKey('pdf_annotations.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Content
    comment = Column(Text, nullable=False)
    
    # Threading
    parent_reply_id = Column(UUID(as_uuid=True), ForeignKey('annotation_replies.id'))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    annotation = relationship("PDFAnnotation", back_populates="replies")
    user = relationship("User", foreign_keys=[user_id])
    parent_reply = relationship("AnnotationReply", remote_side=[id])

class PDFCache(Base):
    """Model for caching downloaded PDFs"""
    __tablename__ = 'pdf_cache'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey('papers.id'), nullable=False)
    
    # Storage details
    file_path = Column(String(500))  # Local file path or S3 key
    file_size = Column(Integer)  # Size in bytes
    file_hash = Column(String(64))  # SHA256 hash
    
    # Metadata
    page_count = Column(Integer)
    pdf_version = Column(String(10))
    is_text_extractable = Column(Boolean, default=True)
    extracted_text = Column(Text)  # Full text for search
    
    # Status
    download_status = Column(String(20), default='pending')  # pending, downloading, completed, failed
    error_message = Column(Text)
    
    # Timestamps
    downloaded_at = Column(DateTime)
    last_accessed = Column(DateTime)
    expires_at = Column(DateTime)  # For cache management
    
    # Relationships
    paper = relationship("Paper", foreign_keys=[paper_id])
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('paper_id', name='uq_pdf_cache_paper'),
        Index('idx_pdf_cache_status', 'download_status'),
    )