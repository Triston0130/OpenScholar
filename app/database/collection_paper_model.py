"""
Extended model for collection_papers association with AI processing support
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

class CollectionPaper(Base):
    """Extended association model for papers in collections with AI metadata"""
    __tablename__ = 'collection_papers_extended'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey('collections.id'), nullable=False)
    paper_id = Column(UUID(as_uuid=True), ForeignKey('papers.id'), nullable=False)
    folder_id = Column(UUID(as_uuid=True), ForeignKey('folders.id'))
    
    # User-added metadata
    notes = Column(Text)
    tags = Column(JSON)  # List of strings
    
    # AI-generated metadata
    ai_notes = Column(Text)
    ai_tags = Column(JSON)  # List of strings
    ai_processed_at = Column(DateTime)
    ai_model_used = Column(String(50))
    
    # Timestamps
    added_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Paper data cache (for performance)
    paper_data = Column(JSON)  # Cached paper information
    
    # Relationships
    collection = relationship("Collection", back_populates="paper_associations")
    paper = relationship("Paper", back_populates="collection_associations")
    
    def __repr__(self):
        return f"<CollectionPaper(collection_id='{self.collection_id}', paper_id='{self.paper_id}')>"


class Folder(Base):
    """Folder model for organizing papers within collections"""
    __tablename__ = 'folders'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    collection_id = Column(UUID(as_uuid=True), ForeignKey('collections.id'), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collection = relationship("Collection", back_populates="folders")
    papers = relationship("CollectionPaper", backref="folder")
    
    def __repr__(self):
        return f"<Folder(name='{self.name}', collection_id='{self.collection_id}')>"