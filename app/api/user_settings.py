# app/api/user_settings.py
"""
API endpoints for user settings including email configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from pydantic import BaseModel, EmailStr

from ..database import get_db
from ..database.models import User
from ..database.user_settings import UserEmailSettings, UserNotificationPreferences
from .auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Pydantic models
class EmailSettingsRequest(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    from_email: Optional[str] = None
    from_name: Optional[str] = "OpenScholar User"

class EmailSettingsResponse(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    from_email: Optional[str]
    from_name: str
    is_configured: bool
    is_verified: bool

class NotificationPreferencesRequest(BaseModel):
    share_invitations: bool = True
    share_acceptances: bool = True
    annotation_replies: bool = True
    collection_updates: bool = True

@router.get("/email")
async def get_email_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> EmailSettingsResponse:
    """Get current user's email settings"""
    
    settings = db.query(UserEmailSettings).filter(
        UserEmailSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        return EmailSettingsResponse(
            smtp_host="",
            smtp_port=587,
            smtp_user="",
            from_email=None,
            from_name="OpenScholar User",
            is_configured=False,
            is_verified=False
        )
    
    return EmailSettingsResponse(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        from_email=settings.from_email,
        from_name=settings.from_name,
        is_configured=settings.is_configured,
        is_verified=settings.is_verified
    )

@router.post("/email")
async def update_email_settings(
    request: EmailSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's email settings"""
    
    settings = db.query(UserEmailSettings).filter(
        UserEmailSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = UserEmailSettings(user_id=current_user.id)
        db.add(settings)
    
    # Update settings
    settings.smtp_host = request.smtp_host
    settings.smtp_port = request.smtp_port
    settings.smtp_user = request.smtp_user
    settings.smtp_password = request.smtp_password  # Should be encrypted in production
    settings.smtp_use_tls = request.smtp_use_tls
    settings.smtp_use_ssl = request.smtp_use_ssl
    settings.from_email = request.from_email or request.smtp_user
    settings.from_name = request.from_name
    settings.is_configured = True
    settings.is_verified = False  # Need to verify
    
    db.commit()
    
    return {"message": "Email settings updated successfully"}

@router.post("/email/test")
async def test_email_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test email settings by sending a test email"""
    
    settings = db.query(UserEmailSettings).filter(
        UserEmailSettings.user_id == current_user.id
    ).first()
    
    if not settings or not settings.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Email settings not configured"
        )
    
    try:
        # Create test message
        msg = MIMEText("This is a test email from OpenScholar to verify your email settings.")
        msg['Subject'] = 'OpenScholar Email Test'
        msg['From'] = f"{settings.from_name} <{settings.from_email}>"
        msg['To'] = current_user.email
        
        # Send email
        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            if settings.smtp_use_tls:
                server.starttls()
        
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        
        # Mark as verified
        settings.is_verified = True
        db.commit()
        
        return {"message": "Test email sent successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to send test email: {str(e)}"
        )

@router.delete("/email")
async def delete_email_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user's email settings"""
    
    settings = db.query(UserEmailSettings).filter(
        UserEmailSettings.user_id == current_user.id
    ).first()
    
    if settings:
        db.delete(settings)
        db.commit()
    
    return {"message": "Email settings deleted"}

@router.get("/notifications")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> NotificationPreferencesRequest:
    """Get user's notification preferences"""
    
    prefs = db.query(UserNotificationPreferences).filter(
        UserNotificationPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        return NotificationPreferencesRequest()
    
    return NotificationPreferencesRequest(
        share_invitations=prefs.share_invitations,
        share_acceptances=prefs.share_acceptances,
        annotation_replies=prefs.annotation_replies,
        collection_updates=prefs.collection_updates
    )

@router.post("/notifications")
async def update_notification_preferences(
    request: NotificationPreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's notification preferences"""
    
    prefs = db.query(UserNotificationPreferences).filter(
        UserNotificationPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = UserNotificationPreferences(user_id=current_user.id)
        db.add(prefs)
    
    prefs.share_invitations = request.share_invitations
    prefs.share_acceptances = request.share_acceptances
    prefs.annotation_replies = request.annotation_replies
    prefs.collection_updates = request.collection_updates
    
    db.commit()
    
    return {"message": "Notification preferences updated"}