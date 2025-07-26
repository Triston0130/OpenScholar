# app/database/user_settings.py
"""
User settings models including email configuration
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .models import Base

class UserEmailSettings(Base):
    """Model for user-specific email settings"""
    __tablename__ = 'user_email_settings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), unique=True, nullable=False)
    
    # SMTP Configuration
    smtp_host = Column(String(255))
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(255))
    smtp_password = Column(Text)  # Should be encrypted in production
    smtp_use_tls = Column(Boolean, default=True)
    smtp_use_ssl = Column(Boolean, default=False)
    
    # Email settings
    from_email = Column(String(255))  # Optional: defaults to smtp_user
    from_name = Column(String(255), default="OpenScholar User")
    
    # Status
    is_configured = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    last_verified_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="email_settings")

class UserNotificationPreferences(Base):
    """Model for user notification preferences"""
    __tablename__ = 'user_notification_preferences'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), unique=True, nullable=False)
    
    # Notification types
    share_invitations = Column(Boolean, default=True)
    share_acceptances = Column(Boolean, default=True)
    annotation_replies = Column(Boolean, default=True)
    collection_updates = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")