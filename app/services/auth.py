from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import secrets
import hashlib
import jwt
import os
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.models import User, UserSession
from app.database.connection import get_db
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))  # In production, load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30


class AuthService:
    """Handles user authentication and session management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    async def register_user(
        self, 
        db: Session,
        email: str, 
        username: str, 
        password: str,
        full_name: Optional[str] = None,
        institution: Optional[str] = None
    ) -> Tuple[Optional[User], Optional[str]]:
        """Register a new user"""
        # Check if email or username already exists
        existing = db.query(User).filter(
            or_(User.email == email, User.username == username)
        ).first()
        
        if existing:
            if existing.email == email:
                return None, "Email already registered"
            else:
                return None, "Username already taken"
        
        # Create new user
        user = User(
            email=email,
            username=username,
            password_hash=self.hash_password(password),
            full_name=full_name,
            institution=institution,
            verification_token=secrets.token_urlsafe(32)
        )
        
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New user registered: {username}")
            return user, None
        except Exception as e:
            db.rollback()
            logger.error(f"Error registering user: {e}")
            return None, "Registration failed"
    
    async def login_user(
        self, 
        db: Session,
        email_or_username: str, 
        password: str,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Authenticate user and create session"""
        # Find user by email or username
        user = db.query(User).filter(
            or_(User.email == email_or_username, User.username == email_or_username)
        ).first()
        
        if not user:
            return None, "Invalid credentials"
        
        if not self.verify_password(password, user.password_hash):
            return None, "Invalid credentials"
        
        if not user.is_active:
            return None, "Account is disabled"
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        
        # Create tokens
        token_data = {
            "sub": user.uid,
            "username": user.username,
            "email": user.email
        }
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        # Create session
        session = UserSession(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        try:
            db.add(session)
            db.commit()
            
            logger.info(f"User logged in: {user.username}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "uid": user.uid,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "institution": user.institution
                }
            }, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating session: {e}")
            return None, "Login failed"
    
    async def refresh_access_token(
        self, 
        db: Session,
        refresh_token: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Create new access token from refresh token"""
        payload = self.decode_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            return None, "Invalid refresh token"
        
        # Find active session with this refresh token
        session = db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token,
            UserSession.is_active == True
        ).first()
        
        if not session:
            return None, "Session not found"
        
        if session.expires_at < datetime.now(timezone.utc):
            session.is_active = False
            db.commit()
            return None, "Session expired"
        
        # Create new access token
        user = session.user
        token_data = {
            "sub": user.uid,
            "username": user.username,
            "email": user.email
        }
        new_access_token = self.create_access_token(token_data)
        
        # Update session
        session.access_token = new_access_token
        session.last_activity = datetime.now(timezone.utc)
        
        try:
            db.commit()
            return new_access_token, None
        except Exception as e:
            db.rollback()
            logger.error(f"Error refreshing token: {e}")
            return None, "Token refresh failed"
    
    async def logout_user(self, db: Session, access_token: str) -> bool:
        """Logout user by invalidating session"""
        # Find and deactivate session
        session = db.query(UserSession).filter(
            UserSession.access_token == access_token,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.is_active = False
            try:
                db.commit()
                logger.info(f"User logged out: {session.user.username}")
                return True
            except Exception as e:
                db.rollback()
                logger.error(f"Error logging out: {e}")
        
        return False
    
    async def get_current_user(self, db: Session, access_token: str) -> Optional[User]:
        """Get user from access token"""
        payload = self.decode_token(access_token)
        
        if not payload or payload.get("type") != "access":
            return None
        
        user_uid = payload.get("sub")
        if not user_uid:
            return None
        
        # Verify session is still active
        session = db.query(UserSession).filter(
            UserSession.access_token == access_token,
            UserSession.is_active == True
        ).first()
        
        if not session:
            return None
        
        # Update last activity
        session.last_activity = datetime.now(timezone.utc)
        db.commit()
        
        return session.user
    
    async def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions"""
        expired_count = 0
        
        expired_sessions = db.query(UserSession).filter(
            UserSession.expires_at < datetime.now(timezone.utc)
        ).all()
        
        for session in expired_sessions:
            session.is_active = False
            expired_count += 1
        
        try:
            db.commit()
            logger.info(f"Cleaned up {expired_count} expired sessions")
            return expired_count
        except Exception as e:
            db.rollback()
            logger.error(f"Error cleaning up sessions: {e}")
            return 0


# Global auth service instance
auth_service = AuthService()