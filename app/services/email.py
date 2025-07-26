# app/services/email.py
"""
Email service for sending notifications
"""

import os
import logging
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import aiosmtplib
from jinja2 import Template

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        # Default/fallback configuration from environment
        self.default_smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.default_smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.default_smtp_user = os.getenv("SMTP_USER", "")
        self.default_smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.default_from_email = os.getenv("FROM_EMAIL", self.default_smtp_user)
        self.default_from_name = os.getenv("FROM_NAME", "OpenScholar")
        self.app_url = os.getenv("APP_URL", "http://localhost:3000")
        
        # Check if default email is configured
        self.has_default_config = bool(self.default_smtp_user and self.default_smtp_password)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        user_settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send an email asynchronously"""
        
        # Use user settings if provided, otherwise fall back to defaults
        smtp_host = user_settings.get('smtp_host', self.default_smtp_host) if user_settings else self.default_smtp_host
        smtp_port = user_settings.get('smtp_port', self.default_smtp_port) if user_settings else self.default_smtp_port
        smtp_user = user_settings.get('smtp_user', self.default_smtp_user) if user_settings else self.default_smtp_user
        smtp_password = user_settings.get('smtp_password', self.default_smtp_password) if user_settings else self.default_smtp_password
        from_email = user_settings.get('from_email', smtp_user) if user_settings else self.default_from_email
        from_name = user_settings.get('from_name', 'OpenScholar User') if user_settings else self.default_from_name
        
        if not smtp_user or not smtp_password:
            logger.warning(f"Email not sent to {to_email} - no email configuration available")
            return False
        
        logger.info(f"Attempting to send email via {smtp_host}:{smtp_port} from {from_email}")
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{from_name} <{from_email}>"
            message["To"] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email based on SSL/TLS settings
            smtp_use_ssl = user_settings.get('smtp_use_ssl', False) if user_settings else False
            smtp_use_tls = user_settings.get('smtp_use_tls', True) if user_settings else True
            
            logger.info(f"Email config: SSL={smtp_use_ssl}, TLS={smtp_use_tls}")
            
            if smtp_use_ssl:
                # Use SSL (typically port 465)
                logger.info("Using SSL connection")
                async with aiosmtplib.SMTP(hostname=smtp_host, port=smtp_port, use_tls=True) as smtp:
                    await smtp.login(smtp_user, smtp_password)
                    await smtp.send_message(message)
            else:
                # Use plain connection with optional STARTTLS (typically port 587)
                logger.info("Using plain connection with STARTTLS" if smtp_use_tls else "Using plain connection")
                
                # Special handling for Gmail and similar services
                if smtp_host == "smtp.gmail.com" and smtp_port == 587:
                    logger.info("Using Gmail-specific configuration")
                    # For Gmail, use the synchronous approach that works in test emails
                    import smtplib
                    from email.mime.multipart import MIMEMultipart as SyncMIMEMultipart
                    
                    server = smtplib.SMTP(smtp_host, smtp_port)
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    
                    # Convert async message to sync format
                    sync_msg = SyncMIMEMultipart("alternative")
                    sync_msg["Subject"] = message["Subject"]
                    sync_msg["From"] = message["From"]
                    sync_msg["To"] = message["To"]
                    
                    for part in message.get_payload():
                        sync_msg.attach(part)
                    
                    server.send_message(sync_msg)
                    server.quit()
                else:
                    # Standard async approach for other servers
                    async with aiosmtplib.SMTP(hostname=smtp_host, port=smtp_port) as smtp:
                        if smtp_use_tls:
                            await smtp.starttls()
                        await smtp.login(smtp_user, smtp_password)
                        await smtp.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_email_sync(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email synchronously (for non-async contexts)"""
        
        if not self.is_configured:
            logger.warning(f"Email not sent to {to_email} - email service not configured")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_share_invitation(
        self,
        to_email: str,
        sharer_name: str,
        collection_name: str,
        role: str,
        message: Optional[str] = None,
        share_id: Optional[str] = None,
        expires_at: Optional[str] = None,
        user_settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a collection share invitation email"""
        
        subject = f"{sharer_name} shared a collection with you on OpenScholar"
        
        # HTML template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #4A90E2; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background-color: #f9f9f9; }
                .button { display: inline-block; padding: 12px 24px; background-color: #4A90E2; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
                .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
                .message-box { background-color: #fff; padding: 15px; border-left: 4px solid #4A90E2; margin: 15px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Collection Shared with You</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    
                    <p><strong>{{ sharer_name }}</strong> has shared the collection <strong>"{{ collection_name }}"</strong> with you on OpenScholar.</p>
                    
                    <p>You've been granted <strong>{{ role }}</strong> access to this collection.</p>
                    
                    {% if message %}
                    <div class="message-box">
                        <p><strong>Message from {{ sharer_name }}:</strong></p>
                        <p>{{ message }}</p>
                    </div>
                    {% endif %}
                    
                    {% if share_id %}
                    <p style="text-align: center;">
                        <a href="{{ app_url }}/accept-share/{{ share_id }}" class="button">Accept Invitation</a>
                    </p>
                    {% endif %}
                    
                    {% if expires_at %}
                    <p style="text-align: center; color: #666; font-size: 14px;">
                        This invitation expires on {{ expires_at }}
                    </p>
                    {% endif %}
                    
                    <p>If you don't have an OpenScholar account yet, you'll need to create one to access this collection.</p>
                </div>
                <div class="footer">
                    <p>© 2024 OpenScholar. All rights reserved.</p>
                    <p>If you didn't expect this email, you can safely ignore it.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text template
        text_template = """
        Collection Shared with You
        
        Hi there,
        
        {{ sharer_name }} has shared the collection "{{ collection_name }}" with you on OpenScholar.
        
        You've been granted {{ role }} access to this collection.
        
        {% if message %}
        Message from {{ sharer_name }}:
        {{ message }}
        {% endif %}
        
        {% if share_id %}
        Accept this invitation: {{ app_url }}/accept-share/{{ share_id }}
        {% endif %}
        
        {% if expires_at %}
        This invitation expires on {{ expires_at }}
        {% endif %}
        
        If you don't have an OpenScholar account yet, you'll need to create one to access this collection.
        
        ---
        © 2024 OpenScholar. All rights reserved.
        If you didn't expect this email, you can safely ignore it.
        """
        
        # Render templates
        html_content = Template(html_template).render(
            sharer_name=sharer_name,
            collection_name=collection_name,
            role=role,
            message=message,
            share_id=share_id,
            expires_at=expires_at,
            app_url=self.app_url
        )
        
        text_content = Template(text_template).render(
            sharer_name=sharer_name,
            collection_name=collection_name,
            role=role,
            message=message,
            share_id=share_id,
            expires_at=expires_at,
            app_url=self.app_url
        )
        
        return await self.send_email(to_email, subject, html_content, text_content, user_settings)
    
    async def send_share_link_created(
        self,
        to_email: str,
        collection_name: str,
        share_link: str,
        role: str,
        expires_at: Optional[str] = None,
        user_settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send email confirming share link creation"""
        
        subject = f"Share link created for '{collection_name}'"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background-color: #4A90E2; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background-color: #f9f9f9; }
                .link-box { background-color: #fff; padding: 15px; border: 1px solid #ddd; margin: 15px 0; word-break: break-all; }
                .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Share Link Created</h1>
                </div>
                <div class="content">
                    <p>Your share link for <strong>"{{ collection_name }}"</strong> has been created successfully.</p>
                    
                    <p>Anyone with this link can access your collection with <strong>{{ role }}</strong> permissions:</p>
                    
                    <div class="link-box">
                        <code>{{ share_link }}</code>
                    </div>
                    
                    {% if expires_at %}
                    <p style="color: #666; font-size: 14px;">
                        This link expires on {{ expires_at }}
                    </p>
                    {% endif %}
                    
                    <p>You can manage or revoke this share link at any time from your collection settings.</p>
                </div>
                <div class="footer">
                    <p>© 2024 OpenScholar. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_content = Template(html_template).render(
            collection_name=collection_name,
            share_link=f"{self.app_url}/shared/{share_link}",
            role=role,
            expires_at=expires_at
        )
        
        return await self.send_email(to_email, subject, html_content)

# Create a singleton instance
email_service = EmailService()