# app/api/sharing.py
"""
API endpoints for collection/folder sharing and PDF annotations
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import asyncio
import uuid

from ..database import get_db
from ..database.models import User, Collection, Paper, collection_papers
from ..database.sharing_models import (
    CollectionShare, FolderShare, ShareRole, 
    PDFAnnotation, AnnotationReply, PDFCache
)
from ..database.user_settings import UserEmailSettings
from .auth import get_current_user
from ..models import BaseModel
from pydantic import EmailStr
from ..services.email import email_service

router = APIRouter(prefix="/api", tags=["sharing"])

# Pydantic models for requests/responses
class ShareCollectionRequest(BaseModel):
    email: Optional[EmailStr] = None
    role: ShareRole = ShareRole.VIEWER
    can_reshare: bool = False
    message: Optional[str] = None
    expires_in_days: Optional[int] = None
    share_type: str  # 'user' or 'link'

class PDFAnnotationRequest(BaseModel):
    paper_id: str
    collection_id: Optional[str] = None
    annotation_type: str  # highlight, comment, note
    color: str = "#FFFF00"
    page_number: int
    position_x: float
    position_y: float
    width: float
    height: float
    selected_text: str
    comment: Optional[str] = None
    is_private: bool = True
    shared_in_collection: bool = False

class AnnotationReplyRequest(BaseModel):
    comment: str
    parent_reply_id: Optional[str] = None

# Collection Sharing Endpoints
@router.post("/collections/{collection_id}/share")
async def share_collection(
    collection_id: str,
    request: ShareCollectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share a collection with another user or create a share link"""
    
    # Check if user owns the collection
    # Convert string ID to UUID if needed
    try:
        collection_uuid = uuid.UUID(collection_id) if isinstance(collection_id, str) else collection_id
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid collection ID format")
    
    collection = db.query(Collection).filter(
        Collection.id == collection_uuid,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if request.share_type == "link":
        # Create a share link
        share_link = secrets.token_urlsafe(16)
        
        share = CollectionShare(
            collection_id=collection_uuid,
            shared_by_user_id=current_user.id,
            role=request.role,
            can_reshare=request.can_reshare,
            share_link=share_link,
            expires_at=datetime.utcnow() + timedelta(days=request.expires_in_days) if request.expires_in_days else None
        )
        
        db.add(share)
        db.commit()
        
        # Get user's email settings
        email_settings = db.query(UserEmailSettings).filter(
            UserEmailSettings.user_id == current_user.id
        ).first()
        
        if email_settings and email_settings.is_configured:
            # Send email notification to the collection owner
            user_settings_dict = {
                'smtp_host': email_settings.smtp_host,
                'smtp_port': email_settings.smtp_port,
                'smtp_user': email_settings.smtp_user,
                'smtp_password': email_settings.smtp_password,
                'from_email': email_settings.from_email,
                'from_name': email_settings.from_name
            }
            
            background_tasks.add_task(
                email_service.send_share_link_created,
                current_user.email,
                collection.name,
                share_link,
                request.role,
                share.expires_at.isoformat() if share.expires_at else None,
                user_settings_dict
            )
        
        return {
            "share_link": f"/shared/{share_link}",
            "expires_at": share.expires_at
        }
    
    else:
        # Share with specific user
        if not request.email:
            raise HTTPException(status_code=400, detail="Email required for user sharing")
        
        # Check if already shared
        existing_share = db.query(CollectionShare).filter(
            CollectionShare.collection_id == collection_uuid,
            CollectionShare.shared_with_email == request.email
        ).first()
        
        if existing_share:
            raise HTTPException(status_code=400, detail="Already shared with this user")
        
        # Find user by email (if they exist)
        target_user = db.query(User).filter(User.email == request.email).first()
        
        share = CollectionShare(
            collection_id=collection_uuid,
            shared_by_user_id=current_user.id,
            shared_with_user_id=target_user.id if target_user else None,
            shared_with_email=request.email,
            role=request.role,
            can_reshare=request.can_reshare,
            message=request.message,
            expires_at=datetime.utcnow() + timedelta(days=request.expires_in_days) if request.expires_in_days else None
        )
        
        db.add(share)
        db.commit()
        db.refresh(share)
        
        # Get user's email settings
        email_settings = db.query(UserEmailSettings).filter(
            UserEmailSettings.user_id == current_user.id
        ).first()
        
        if email_settings and email_settings.is_configured:
            # Send email notification
            user_settings_dict = {
                'smtp_host': email_settings.smtp_host,
                'smtp_port': email_settings.smtp_port,
                'smtp_user': email_settings.smtp_user,
                'smtp_password': email_settings.smtp_password,
                'from_email': email_settings.from_email,
                'from_name': email_settings.from_name,
                'smtp_use_tls': email_settings.smtp_use_tls,
                'smtp_use_ssl': email_settings.smtp_use_ssl
            }
            
            print(f"[DEBUG] Email settings configured for user {current_user.username}")
            print(f"[DEBUG] Sending share invitation to {request.email}")
            print(f"[DEBUG] Share type: {request.share_type}")
            
            if request.share_type == 'user' and request.email:
                # Send email directly without wrapper function
                print(f"[DEBUG] About to send email to {request.email}")
                background_tasks.add_task(
                    email_service.send_share_invitation,
                    request.email,
                    current_user.full_name or current_user.username,
                    collection.name,
                    request.role,
                    request.message,
                    str(share.id) if target_user else None,
                    share.expires_at.isoformat() if share.expires_at else None,
                    user_settings_dict
                )
                print(f"[DEBUG] Email task added to background queue")
            elif request.share_type == 'link':
                # For link sharing, send confirmation to the sharer
                background_tasks.add_task(
                    email_service.send_share_link_created,
                    current_user.email,
                    collection.name,
                    share.share_token,
                    request.role,
                    share.expires_at.isoformat() if share.expires_at else None,
                    user_settings_dict
                )
                print(f"[DEBUG] Link share confirmation email task added")
        else:
            print(f"[DEBUG] Email settings not configured for user {current_user.username}")
        
        if request.share_type == 'link':
            return {
                "message": "Share link created successfully", 
                "share_id": str(share.id),
                "share_link": f"/shared/{share.share_token}"
            }
        else:
            return {"message": f"Collection shared with {request.email}", "share_id": str(share.id)}

@router.get("/collections/{collection_id}/shares")
async def get_collection_shares(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users with whom a collection is shared"""
    
    # Check if user has access to view shares
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Check if user is owner or has admin access
    if collection.user_id != current_user.id:
        admin_share = db.query(CollectionShare).filter(
            CollectionShare.collection_id == collection_id,
            CollectionShare.shared_with_user_id == current_user.id,
            CollectionShare.role == ShareRole.ADMIN
        ).first()
        
        if not admin_share:
            raise HTTPException(status_code=403, detail="Not authorized to view shares")
    
    shares = db.query(CollectionShare).filter(
        CollectionShare.collection_id == collection_id
    ).all()
    
    return shares

@router.get("/collections/{collection_id}/collaborators")
async def get_collection_collaborators(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users who have access to a collection (owner + shared users)"""
    
    # Check if user has access to this collection
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Check if user has access
    has_access = collection.user_id == current_user.id
    if not has_access:
        share = db.query(CollectionShare).filter(
            CollectionShare.collection_id == collection_id,
            CollectionShare.shared_with_user_id == current_user.id,
            CollectionShare.accepted == True
        ).first()
        if not share:
            raise HTTPException(status_code=403, detail="No access to this collection")
    
    collaborators = []
    
    # Add owner
    owner = db.query(User).filter(User.id == collection.user_id).first()
    if owner:
        collaborators.append({
            "id": str(owner.id),
            "name": owner.name,
            "email": owner.email,
            "role": "owner",
            "avatar_url": None  # Add avatar support later
        })
    
    # Add shared users
    shares = db.query(CollectionShare).filter(
        CollectionShare.collection_id == collection_id,
        CollectionShare.accepted == True
    ).all()
    
    for share in shares:
        if share.shared_with_user_id:
            user = db.query(User).filter(User.id == share.shared_with_user_id).first()
            if user:
                collaborators.append({
                    "id": str(user.id),
                    "name": user.name,
                    "email": user.email,
                    "role": share.role.value,
                    "avatar_url": None
                })
    
    return collaborators

@router.delete("/collections/{collection_id}/shares/{share_id}")
async def remove_collection_share(
    collection_id: str,
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a user's access to a collection"""
    
    # Check ownership
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found or not authorized")
    
    share = db.query(CollectionShare).filter(
        CollectionShare.id == share_id,
        CollectionShare.collection_id == collection_id
    ).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    db.delete(share)
    db.commit()
    
    return {"message": "Share removed successfully"}

# Share acceptance/rejection endpoints
@router.post("/shares/{share_id}/accept")
async def accept_share(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a collection share invitation"""
    
    share = db.query(CollectionShare).filter(
        CollectionShare.id == share_id,
        CollectionShare.shared_with_user_id == current_user.id
    ).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share invitation not found")
    
    if share.accepted:
        raise HTTPException(status_code=400, detail="Share already accepted")
    
    if share.expires_at and share.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Share invitation has expired")
    
    share.accepted = True
    share.accepted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Share accepted successfully", "collection_id": str(share.collection_id)}

@router.post("/shares/{share_id}/reject")
async def reject_share(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a collection share invitation"""
    
    share = db.query(CollectionShare).filter(
        CollectionShare.id == share_id,
        CollectionShare.shared_with_user_id == current_user.id
    ).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share invitation not found")
    
    db.delete(share)
    db.commit()
    
    return {"message": "Share rejected successfully"}

@router.get("/shares/pending")
async def get_pending_shares(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending share invitations for the current user"""
    
    shares = db.query(CollectionShare).filter(
        CollectionShare.shared_with_user_id == current_user.id,
        CollectionShare.accepted == False
    ).all()
    
    # Include collection details
    results = []
    for share in shares:
        collection = db.query(Collection).filter(Collection.id == share.collection_id).first()
        if collection:
            shared_by = db.query(User).filter(User.id == share.shared_by_user_id).first()
            results.append({
                "share_id": str(share.id),
                "collection_id": str(share.collection_id),
                "collection_name": collection.name,
                "collection_description": collection.description,
                "shared_by": {
                    "id": str(shared_by.id) if shared_by else None,
                    "name": shared_by.name if shared_by else "Unknown",
                    "email": shared_by.email if shared_by else None
                },
                "role": share.role.value,
                "can_reshare": share.can_reshare,
                "message": share.message,
                "shared_at": share.created_at,
                "expires_at": share.expires_at
            })
    
    return results

@router.get("/collections/shared")
async def get_shared_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all collections shared with the current user"""
    
    shares = db.query(CollectionShare).filter(
        CollectionShare.shared_with_user_id == current_user.id,
        CollectionShare.accepted == True
    ).all()
    
    collections = []
    for share in shares:
        collection = db.query(Collection).filter(Collection.id == share.collection_id).first()
        if collection:
            owner = db.query(User).filter(User.id == collection.user_id).first()
            # Count papers in the collection using the association table
            paper_count = db.query(collection_papers).filter(
                collection_papers.c.collection_id == collection.id
            ).count()
            
            collections.append({
                "id": str(collection.id),
                "name": collection.name,
                "description": collection.description,
                "color": collection.color,
                "icon": collection.icon,
                "paper_count": paper_count,
                "owner": {
                    "id": str(owner.id) if owner else None,
                    "name": owner.name if owner else "Unknown",
                    "email": owner.email if owner else None
                },
                "my_role": share.role.value,
                "can_reshare": share.can_reshare,
                "accepted_at": share.accepted_at,
                "created_at": collection.created_at,
                "updated_at": collection.updated_at
            })
    
    return collections

@router.post("/shares/link/{share_link}")
async def accept_share_link(
    share_link: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a collection via share link"""
    
    # Find the share by link
    share = db.query(CollectionShare).filter(
        CollectionShare.share_link == share_link
    ).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Invalid share link")
    
    if share.expires_at and share.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Share link has expired")
    
    # Check if user already has access
    existing_share = db.query(CollectionShare).filter(
        CollectionShare.collection_id == share.collection_id,
        CollectionShare.shared_with_user_id == current_user.id
    ).first()
    
    if existing_share:
        if existing_share.accepted:
            return {
                "message": "You already have access to this collection",
                "collection_id": str(share.collection_id)
            }
        else:
            # Accept the existing share
            existing_share.accepted = True
            existing_share.accepted_at = datetime.utcnow()
            db.commit()
            return {
                "message": "Share accepted successfully",
                "collection_id": str(share.collection_id)
            }
    
    # Create new share for this user
    new_share = CollectionShare(
        collection_id=share.collection_id,
        shared_by_user_id=share.shared_by_user_id,
        shared_with_user_id=current_user.id,
        shared_with_email=current_user.email,
        role=share.role,
        can_reshare=share.can_reshare,
        accepted=True,
        accepted_at=datetime.utcnow()
    )
    
    db.add(new_share)
    db.commit()
    
    return {
        "message": "Collection shared successfully",
        "collection_id": str(share.collection_id)
    }

@router.get("/shares/link/{share_link}/info")
async def get_share_link_info(
    share_link: str,
    db: Session = Depends(get_db)
):
    """Get information about a share link (public endpoint)"""
    
    share = db.query(CollectionShare).filter(
        CollectionShare.share_link == share_link
    ).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Invalid share link")
    
    if share.expires_at and share.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Share link has expired")
    
    collection = db.query(Collection).filter(Collection.id == share.collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    owner = db.query(User).filter(User.id == collection.user_id).first()
    
    return {
        "collection": {
            "id": str(collection.id),
            "name": collection.name,
            "description": collection.description,
            "paper_count": db.query(collection_papers).filter(
                collection_papers.c.collection_id == collection.id
            ).count()
        },
        "owner": {
            "name": owner.name if owner else "Unknown"
        },
        "role": share.role.value,
        "expires_at": share.expires_at
    }

# PDF Annotation Endpoints
@router.post("/papers/{paper_id}/annotations")
async def create_annotation(
    paper_id: str,
    request: PDFAnnotationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new PDF annotation"""
    
    # Verify paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    annotation = PDFAnnotation(
        paper_id=paper_id,
        user_id=current_user.id,
        collection_id=request.collection_id,
        annotation_type=request.annotation_type,
        color=request.color,
        page_number=request.page_number,
        position_x=request.position_x,
        position_y=request.position_y,
        width=request.width,
        height=request.height,
        selected_text=request.selected_text,
        comment=request.comment,
        is_private=request.is_private,
        shared_in_collection=request.shared_in_collection
    )
    
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    
    return annotation

@router.get("/papers/{paper_id}/annotations")
async def get_paper_annotations(
    paper_id: str,
    collection_id: Optional[str] = None,
    include_shared: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get annotations for a paper (including shared ones if user has access)"""
    
    # Base query
    query = db.query(PDFAnnotation).filter(PDFAnnotation.paper_id == paper_id)
    
    if collection_id:
        # Check if user has access to this collection
        has_access = db.query(Collection).filter(
            Collection.id == collection_id,
            Collection.user_id == current_user.id
        ).first()
        
        if not has_access:
            # Check if collection is shared with user
            share = db.query(CollectionShare).filter(
                CollectionShare.collection_id == collection_id,
                CollectionShare.shared_with_user_id == current_user.id,
                CollectionShare.accepted == True
            ).first()
            
            if not share:
                raise HTTPException(status_code=403, detail="No access to this collection")
        
        # Get all annotations in this collection context
        query = query.filter(PDFAnnotation.collection_id == collection_id)
        
        if include_shared:
            # Include all shared annotations in the collection
            query = query.filter(
                (PDFAnnotation.user_id == current_user.id) |
                (PDFAnnotation.shared_in_collection == True)
            )
        else:
            query = query.filter(PDFAnnotation.user_id == current_user.id)
    else:
        # No collection context - only show user's own annotations
        query = query.filter(PDFAnnotation.user_id == current_user.id)
    
    annotations = query.order_by(PDFAnnotation.page_number, PDFAnnotation.created_at).all()
    
    # Include user info for shared annotations
    for annotation in annotations:
        if annotation.user_id != current_user.id:
            user = db.query(User).filter(User.id == annotation.user_id).first()
            annotation.user_name = user.name if user else "Unknown"
    
    return annotations

@router.put("/annotations/{annotation_id}")
async def update_annotation(
    annotation_id: str,
    comment: Optional[str] = None,
    color: Optional[str] = None,
    is_private: Optional[bool] = None,
    shared_in_collection: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an annotation"""
    
    annotation = db.query(PDFAnnotation).filter(
        PDFAnnotation.id == annotation_id,
        PDFAnnotation.user_id == current_user.id
    ).first()
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    if comment is not None:
        annotation.comment = comment
    if color is not None:
        annotation.color = color
    if is_private is not None:
        annotation.is_private = is_private
    if shared_in_collection is not None:
        annotation.shared_in_collection = shared_in_collection
    
    annotation.updated_at = datetime.utcnow()
    db.commit()
    
    return annotation

@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an annotation"""
    
    annotation = db.query(PDFAnnotation).filter(
        PDFAnnotation.id == annotation_id,
        PDFAnnotation.user_id == current_user.id
    ).first()
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    db.delete(annotation)
    db.commit()
    
    return {"message": "Annotation deleted successfully"}

# Annotation Replies
@router.post("/annotations/{annotation_id}/replies")
async def create_annotation_reply(
    annotation_id: str,
    request: AnnotationReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a reply to an annotation"""
    
    # Verify annotation exists and user has access
    annotation = db.query(PDFAnnotation).filter(PDFAnnotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # Check if user has access (own annotation or shared)
    if annotation.user_id != current_user.id and not annotation.shared_in_collection:
        raise HTTPException(status_code=403, detail="Not authorized to reply to this annotation")
    
    reply = AnnotationReply(
        annotation_id=annotation_id,
        user_id=current_user.id,
        comment=request.comment,
        parent_reply_id=request.parent_reply_id
    )
    
    db.add(reply)
    db.commit()
    db.refresh(reply)
    
    return reply

@router.get("/annotations/{annotation_id}/replies")
async def get_annotation_replies(
    annotation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all replies for an annotation"""
    
    replies = db.query(AnnotationReply).filter(
        AnnotationReply.annotation_id == annotation_id
    ).order_by(AnnotationReply.created_at).all()
    
    return replies

# PDF Cache Management
@router.get("/papers/{paper_id}/pdf-status")
async def get_pdf_status(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if PDF is cached and available"""
    
    pdf_cache = db.query(PDFCache).filter(PDFCache.paper_id == paper_id).first()
    
    if not pdf_cache:
        return {"status": "not_cached", "available": False}
    
    return {
        "status": pdf_cache.download_status,
        "available": pdf_cache.download_status == "completed",
        "page_count": pdf_cache.page_count,
        "file_size": pdf_cache.file_size,
        "cached_at": pdf_cache.downloaded_at
    }

@router.post("/papers/{paper_id}/download-pdf")
async def trigger_pdf_download(
    paper_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger PDF download for caching"""
    
    # Check if paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.pdf_url and not paper.full_text_url:
        raise HTTPException(status_code=400, detail="No PDF URL available for this paper")
    
    # Check if already cached
    existing_cache = db.query(PDFCache).filter(PDFCache.paper_id == paper_id).first()
    if existing_cache and existing_cache.download_status == "completed":
        return {"message": "PDF already cached", "status": "completed"}
    
    # Create cache entry
    if not existing_cache:
        pdf_cache = PDFCache(
            paper_id=paper_id,
            download_status="pending"
        )
        db.add(pdf_cache)
        db.commit()
    
    # TODO: Trigger async download task
    # This would typically use Celery or similar task queue
    
    return {"message": "PDF download initiated", "status": "pending"}