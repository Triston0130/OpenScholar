from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import secrets
import json
import uuid

from app.database.connection import get_db
from app.database.models import User, Collection, Paper, collection_papers
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/collections", tags=["collections"])


def parse_collection_id(collection_id: str):
    """Helper to parse and validate collection ID"""
    try:
        return uuid.UUID(collection_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid collection ID format"
        )


# Request/Response models
class CreateCollectionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    is_public: bool = False


class UpdateCollectionRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    is_public: Optional[bool] = None


class AddPaperRequest(BaseModel):
    paper_data: dict  # Full paper object from search results
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdatePaperNotesRequest(BaseModel):
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class CollectionResponse(BaseModel):
    id: str  # UUID as string for JSON serialization
    name: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    is_public: bool
    share_token: Optional[str]
    paper_count: int
    created_at: datetime
    updated_at: Optional[datetime]


class CollectionPaperResponse(BaseModel):
    id: str  # Paper ID as string
    paper_data: dict
    notes: Optional[str]
    tags: Optional[List[str]]
    added_at: datetime


# Endpoints
@router.get("/", response_model=List[CollectionResponse])
async def get_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all collections for the current user"""
    collections = db.query(Collection).filter(
        Collection.user_id == current_user.id
    ).all()
    
    return [
        CollectionResponse(
            id=str(c.id),
            name=c.name,
            description=c.description,
            color=c.color,
            icon=c.icon,
            is_public=c.is_public,
            share_token=c.share_token,
            paper_count=len(c.papers),
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in collections
    ]


@router.post("/", response_model=CollectionResponse)
async def create_collection(
    request: CreateCollectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new collection"""
    # Check if user already has a collection with this name
    existing = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.name == request.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collection with this name already exists"
        )
    
    # Create collection
    collection = Collection(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        color=request.color or "#3B82F6",  # Default blue
        icon=request.icon,
        is_public=request.is_public,
        share_token=secrets.token_urlsafe(16) if request.is_public else None
    )
    
    try:
        db.add(collection)
        db.commit()
        db.refresh(collection)
        
        return CollectionResponse(
            id=str(collection.id),
            name=collection.name,
            description=collection.description,
            color=collection.color,
            icon=collection.icon,
            is_public=collection.is_public,
            share_token=collection.share_token,
            paper_count=0,
            created_at=collection.created_at,
            updated_at=collection.updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create collection"
        )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific collection"""
    collection_uuid = parse_collection_id(collection_id)
    
    collection = db.query(Collection).filter(
        Collection.id == collection_uuid,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    return CollectionResponse(
        id=str(collection.id),
        name=collection.name,
        description=collection.description,
        color=collection.color,
        icon=collection.icon,
        is_public=collection.is_public,
        share_token=collection.share_token,
        paper_count=len(collection.papers),
        created_at=collection.created_at,
        updated_at=collection.updated_at
    )


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    request: UpdateCollectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a collection"""
    collection_uuid = parse_collection_id(collection_id)
    
    collection = db.query(Collection).filter(
        Collection.id == collection_uuid,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    # Update fields
    if request.name is not None:
        collection.name = request.name
    if request.description is not None:
        collection.description = request.description
    if request.color is not None:
        collection.color = request.color
    if request.icon is not None:
        collection.icon = request.icon
    if request.is_public is not None:
        collection.is_public = request.is_public
        if request.is_public and not collection.share_token:
            collection.share_token = secrets.token_urlsafe(16)
        elif not request.is_public:
            collection.share_token = None
    
    try:
        db.commit()
        db.refresh(collection)
        
        return CollectionResponse(
            id=str(collection.id),
            name=collection.name,
            description=collection.description,
            color=collection.color,
            icon=collection.icon,
            is_public=collection.is_public,
            share_token=collection.share_token,
            paper_count=len(collection.papers),
            created_at=collection.created_at,
            updated_at=collection.updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update collection"
        )


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a collection"""
    collection_uuid = parse_collection_id(collection_id)
    
    collection = db.query(Collection).filter(
        Collection.id == collection_uuid,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    try:
        db.delete(collection)
        db.commit()
        return {"message": "Collection deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete collection"
        )


# Paper management within collections
@router.get("/{collection_id}/papers", response_model=List[CollectionPaperResponse])
async def get_collection_papers(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all papers in a collection"""
    collection_uuid = parse_collection_id(collection_id)
    
    # Verify collection ownership
    collection = db.query(Collection).filter(
        Collection.id == collection_uuid,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    # Query papers with association table data
    stmt = (
        select(Paper, collection_papers.c.notes, collection_papers.c.custom_tags, collection_papers.c.added_at)
        .join(collection_papers, Paper.id == collection_papers.c.paper_id)
        .where(collection_papers.c.collection_id == collection_uuid)
    )
    
    results = db.execute(stmt).all()
    
    return [
        CollectionPaperResponse(
            id=str(paper.id),
            paper_data={
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "year": paper.year,
                "journal": paper.journal,
                "venue": paper.venue,
                "doi": paper.doi,
                "arxiv_id": paper.arxiv_id,
                "url": paper.url,
                "pdf_url": paper.pdf_url,
                "citation_count": paper.citation_count,
                "source": paper.source,
                **({"extra_metadata": paper.extra_metadata} if paper.extra_metadata else {})
            },
            notes=notes,
            tags=custom_tags,
            added_at=added_at
        )
        for paper, notes, custom_tags, added_at in results
    ]


@router.post("/{collection_id}/papers", response_model=CollectionPaperResponse)
async def add_paper_to_collection(
    collection_id: str,
    request: AddPaperRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a paper to a collection"""
    collection_uuid = parse_collection_id(collection_id)
    
    # Verify collection ownership
    collection = db.query(Collection).filter(
        Collection.id == collection_uuid,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    # Extract paper data
    paper_doi = request.paper_data.get("doi")
    paper_title = request.paper_data.get("title", "")
    
    # Check if paper already exists in database by DOI
    existing_paper = None
    if paper_doi:
        existing_paper = db.query(Paper).filter(Paper.doi == paper_doi).first()
    
    # If not found by DOI, try to find by title (case-insensitive)
    if not existing_paper and paper_title:
        existing_paper = db.query(Paper).filter(
            Paper.title.ilike(paper_title)
        ).first()
    
    # Check if paper is already in this collection
    if existing_paper:
        stmt = select(collection_papers).where(
            and_(
                collection_papers.c.collection_id == collection_uuid,
                collection_papers.c.paper_id == existing_paper.id
            )
        )
        if db.execute(stmt).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paper already in collection"
            )
    
    try:
        # Create new paper if it doesn't exist
        if not existing_paper:
            paper = Paper(
                title=paper_title,
                authors=request.paper_data.get("authors", []),
                abstract=request.paper_data.get("abstract"),
                year=request.paper_data.get("year"),
                journal=request.paper_data.get("journal"),
                venue=request.paper_data.get("venue"),
                doi=paper_doi,
                arxiv_id=request.paper_data.get("arxiv_id"),
                pubmed_id=request.paper_data.get("pubmed_id"),
                url=request.paper_data.get("url"),
                pdf_url=request.paper_data.get("pdf_url"),
                citation_count=request.paper_data.get("citation_count"),
                influential_citation_count=request.paper_data.get("influential_citation_count"),
                source=request.paper_data.get("source", "unknown"),
                keywords=request.paper_data.get("keywords"),
                subjects=request.paper_data.get("subjects"),
                publication_type=request.paper_data.get("publication_type"),
                is_open_access=request.paper_data.get("is_open_access"),
                extra_metadata=request.paper_data.get("extra_metadata")
            )
            db.add(paper)
            db.flush()  # Get the paper ID without committing
        else:
            paper = existing_paper
        
        # Add paper to collection via association table
        stmt = collection_papers.insert().values(
            collection_id=collection_uuid,
            paper_id=paper.id,
            notes=request.notes,
            custom_tags=request.tags,
            added_at=datetime.utcnow()
        )
        db.execute(stmt)
        
        # Update collection paper count
        collection.paper_count = db.query(collection_papers).filter(
            collection_papers.c.collection_id == collection_uuid
        ).count()
        
        db.commit()
        
        return CollectionPaperResponse(
            id=str(paper.id),
            paper_data=request.paper_data,
            notes=request.notes,
            tags=request.tags,
            added_at=datetime.utcnow()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add paper to collection: {str(e)}"
        )


@router.put("/{collection_id}/papers/{paper_id}")
async def update_paper_notes(
    collection_id: str,
    paper_id: str,
    request: UpdatePaperNotesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notes and tags for a paper in a collection"""
    collection_uuid = parse_collection_id(collection_id)
    paper_uuid = parse_collection_id(paper_id)  # Reuse the UUID parser
    
    # Verify collection ownership
    collection = db.query(Collection).filter(
        Collection.id == collection_uuid,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    # Verify paper exists in collection
    stmt = select(collection_papers).where(
        and_(
            collection_papers.c.collection_id == collection_uuid,
            collection_papers.c.paper_id == paper_uuid
        )
    )
    
    if not db.execute(stmt).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found in collection"
        )
    
    try:
        # Update the association table
        update_values = {}
        if request.notes is not None:
            update_values["notes"] = request.notes
        if request.tags is not None:
            update_values["custom_tags"] = request.tags
        
        if update_values:
            stmt = (
                collection_papers.update()
                .where(
                    and_(
                        collection_papers.c.collection_id == collection_uuid,
                        collection_papers.c.paper_id == paper_uuid
                    )
                )
                .values(**update_values)
            )
            db.execute(stmt)
        
        db.commit()
        return {"message": "Paper updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update paper: {str(e)}"
        )


@router.delete("/{collection_id}/papers/{paper_id}")
async def remove_paper_from_collection(
    collection_id: str,
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a paper from a collection"""
    collection_uuid = parse_collection_id(collection_id)
    paper_uuid = parse_collection_id(paper_id)  # Reuse the UUID parser
    
    # Verify collection ownership
    collection = db.query(Collection).filter(
        Collection.id == collection_uuid,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    # Verify paper exists in collection
    stmt = select(collection_papers).where(
        and_(
            collection_papers.c.collection_id == collection_uuid,
            collection_papers.c.paper_id == paper_uuid
        )
    )
    
    if not db.execute(stmt).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found in collection"
        )
    
    try:
        # Remove from association table
        stmt = (
            collection_papers.delete()
            .where(
                and_(
                    collection_papers.c.collection_id == collection_uuid,
                    collection_papers.c.paper_id == paper_uuid
                )
            )
        )
        db.execute(stmt)
        
        # Update collection paper count
        collection.paper_count = db.query(collection_papers).filter(
            collection_papers.c.collection_id == collection_uuid
        ).count()
        
        db.commit()
        return {"message": "Paper removed from collection"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove paper: {str(e)}"
        )


# Public collection access
@router.get("/public/{share_token}", response_model=CollectionResponse)
async def get_public_collection(
    share_token: str,
    db: Session = Depends(get_db)
):
    """Get a public collection by share token"""
    collection = db.query(Collection).filter(
        Collection.share_token == share_token,
        Collection.is_public == True
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found or not public"
        )
    
    return CollectionResponse(
        id=str(collection.id),
        name=collection.name,
        description=collection.description,
        color=collection.color,
        icon=collection.icon,
        is_public=collection.is_public,
        share_token=collection.share_token,
        paper_count=len(collection.papers),
        created_at=collection.created_at,
        updated_at=collection.updated_at
    )


@router.get("/public/{share_token}/papers", response_model=List[CollectionPaperResponse])
async def get_public_collection_papers(
    share_token: str,
    db: Session = Depends(get_db)
):
    """Get papers from a public collection"""
    collection = db.query(Collection).filter(
        Collection.share_token == share_token,
        Collection.is_public == True
    ).first()
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found or not public"
        )
    
    # Query papers with association table data
    stmt = (
        select(Paper, collection_papers.c.notes, collection_papers.c.custom_tags, collection_papers.c.added_at)
        .join(collection_papers, Paper.id == collection_papers.c.paper_id)
        .where(collection_papers.c.collection_id == collection.id)
    )
    
    results = db.execute(stmt).all()
    
    return [
        CollectionPaperResponse(
            id=str(paper.id),
            paper_data={
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "year": paper.year,
                "journal": paper.journal,
                "venue": paper.venue,
                "doi": paper.doi,
                "arxiv_id": paper.arxiv_id,
                "url": paper.url,
                "pdf_url": paper.pdf_url,
                "citation_count": paper.citation_count,
                "source": paper.source,
                **({"extra_metadata": paper.extra_metadata} if paper.extra_metadata else {})
            },
            notes=notes,
            tags=custom_tags,
            added_at=added_at
        )
        for paper, notes, custom_tags, added_at in results
    ]