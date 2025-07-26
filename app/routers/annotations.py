from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
from pathlib import Path

router = APIRouter(prefix="/api/annotations", tags=["annotations"])

# In-memory storage for demo (replace with database in production)
ANNOTATIONS_FILE = Path("./data/annotations.json")
ANNOTATIONS_FILE.parent.mkdir(exist_ok=True)

class Annotation(BaseModel):
    id: str
    paperId: str
    pdfUrl: str
    type: str  # 'highlight' | 'note' | 'flashcard'
    text: str
    note: Optional[str] = None
    pageNumber: Optional[int] = None
    position: Optional[Dict[str, float]] = None
    textPosition: Optional[Dict[str, Any]] = None
    color: Optional[str] = None
    colorName: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    # Flashcard specific fields
    front: Optional[str] = None
    back: Optional[str] = None
    nextReviewDate: Optional[datetime] = None
    difficulty: Optional[float] = None

def load_annotations() -> List[Dict[str, Any]]:
    """Load annotations from file"""
    if not ANNOTATIONS_FILE.exists():
        return []
    
    try:
        with open(ANNOTATIONS_FILE, 'r') as f:
            data = json.load(f)
            return data
    except Exception:
        return []

def save_annotations(annotations: List[Dict[str, Any]]):
    """Save annotations to file"""
    with open(ANNOTATIONS_FILE, 'w') as f:
        json.dump(annotations, f, indent=2, default=str)

@router.get("", response_model=List[Annotation])
async def get_annotations(pdf_url: Optional[str] = None):
    """Get all annotations or filter by PDF URL"""
    annotations = load_annotations()
    
    if pdf_url:
        annotations = [a for a in annotations if a.get('pdfUrl') == pdf_url]
    
    return annotations

@router.get("/{annotation_id}", response_model=Annotation)
async def get_annotation(annotation_id: str):
    """Get a specific annotation by ID"""
    annotations = load_annotations()
    
    for ann in annotations:
        if ann.get('id') == annotation_id:
            return ann
    
    raise HTTPException(status_code=404, detail="Annotation not found")

@router.post("", response_model=Annotation)
async def create_annotation(annotation: Annotation):
    """Create a new annotation"""
    annotations = load_annotations()
    
    # Convert to dict and add to list
    ann_dict = annotation.dict()
    annotations.append(ann_dict)
    
    save_annotations(annotations)
    return annotation

@router.put("/{annotation_id}", response_model=Annotation)
async def update_annotation(annotation_id: str, updates: Dict[str, Any]):
    """Update an existing annotation"""
    annotations = load_annotations()
    
    for i, ann in enumerate(annotations):
        if ann.get('id') == annotation_id:
            # Update fields
            ann.update(updates)
            ann['updatedAt'] = datetime.now().isoformat()
            
            save_annotations(annotations)
            return ann
    
    raise HTTPException(status_code=404, detail="Annotation not found")

@router.delete("/{annotation_id}")
async def delete_annotation(annotation_id: str):
    """Delete an annotation"""
    annotations = load_annotations()
    
    filtered = [a for a in annotations if a.get('id') != annotation_id]
    
    if len(filtered) == len(annotations):
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    save_annotations(filtered)
    return {"message": "Annotation deleted successfully"}

@router.post("/sync")
async def sync_annotations(annotations: List[Annotation]):
    """Sync annotations from client"""
    # In a real app, this would merge with existing annotations
    # and handle conflicts
    ann_dicts = [ann.dict() for ann in annotations]
    save_annotations(ann_dicts)
    
    return {"message": f"Synced {len(annotations)} annotations"}

@router.get("/export/{paper_id}")
async def export_annotations(paper_id: str, format: str = "json"):
    """Export annotations for a specific paper"""
    annotations = load_annotations()
    paper_annotations = [a for a in annotations if a.get('paperId') == paper_id]
    
    if format == "json":
        return paper_annotations
    elif format == "markdown":
        # Convert to markdown format
        md_content = f"# Annotations for Paper {paper_id}\n\n"
        
        for ann in paper_annotations:
            md_content += f"## {ann['type'].title()}\n"
            md_content += f"**Text:** {ann['text']}\n"
            if ann.get('note'):
                md_content += f"**Note:** {ann['note']}\n"
            if ann.get('front') and ann.get('back'):
                md_content += f"**Front:** {ann['front']}\n"
                md_content += f"**Back:** {ann['back']}\n"
            md_content += f"*Created: {ann['createdAt']}*\n\n"
        
        return {"content": md_content, "format": "markdown"}
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")