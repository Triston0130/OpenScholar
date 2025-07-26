from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
from pathlib import Path
import shutil
import logging

from app.database.connection import get_db
from app.api.auth import get_current_user_optional
from app.database.models import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = Path("uploads/pdfs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Max file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024

@router.post("/api/upload-pdf")
async def upload_pdf(
    pdf: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Upload a PDF file and return its URL"""
    
    # Log the received content type for debugging
    logger.info(f"Received file upload: filename={pdf.filename}, content_type={pdf.content_type}")
    
    # Validate file type - check both content type and filename extension
    if pdf.content_type not in ["application/pdf", "application/x-pdf"] and not pdf.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail=f"File must be a PDF. Received content_type: {pdf.content_type}")
    
    # Check file size
    try:
        contents = await pdf.read()
        logger.info(f"Read file contents: size={len(contents)} bytes")
    except Exception as e:
        logger.error(f"Error reading file contents: {e}")
        raise HTTPException(status_code=400, detail="Failed to read file contents")
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB")
    
    # Generate unique filename
    file_extension = Path(pdf.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create user-specific directory if user is logged in
    if current_user:
        user_dir = UPLOAD_DIR / str(current_user.id)
        user_dir.mkdir(exist_ok=True)
        file_path = user_dir / unique_filename
    else:
        file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # Generate URL path
        if current_user:
            pdf_url = f"/uploads/pdfs/{current_user.id}/{unique_filename}"
        else:
            pdf_url = f"/uploads/pdfs/{unique_filename}"
        
        logger.info(f"PDF uploaded successfully: {pdf_url}")
        
        return JSONResponse(content={
            "pdf_url": pdf_url,
            "filename": pdf.filename,
            "size": len(contents)
        })
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        # Clean up if upload failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail="Failed to upload PDF")

# File serving is now handled by FastAPI's StaticFiles mount in main.py