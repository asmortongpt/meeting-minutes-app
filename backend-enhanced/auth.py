"""
Enterprise-Grade Authentication & Authorization
OAuth2 + JWT with Refresh Tokens + RBAC
"""
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import secrets
from functools import wraps

from config import settings
from models import User, Role, AuditLog

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Token models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    roles: List[str] = []

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    organization: Optional[str]
    roles: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password with bcrypt (cost=12)"""
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"

    return True, "Password is strong"

# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token (longer expiration)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)  # 30 days for refresh token
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        roles: List[str] = payload.get("roles", [])

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        return TokenData(user_id=user_id, email=email, roles=roles)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# User authentication
def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password"""
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return user

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from token"""
    token_data = verify_token(token)

    user = db.query(User).filter(User.id == token_data.user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Role-Based Access Control (RBAC)
class RoleChecker:
    """Dependency to check if user has required roles"""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)):
        user_roles = [role.name for role in current_user.roles]

        # Check if user has any of the allowed roles
        if not any(role in user_roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(self.allowed_roles)}"
            )

        return current_user

# Convenience role checkers
require_admin = RoleChecker(["admin"])
require_manager = RoleChecker(["admin", "manager"])
require_user = RoleChecker(["admin", "manager", "user"])

# Audit logging
def log_audit_event(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None
):
    """Log audit event for compliance"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        timestamp=datetime.utcnow()
    )

    db.add(audit_log)
    db.commit()

# Rate limiting decorator
from collections import defaultdict
from time import time

# Simple in-memory rate limiter (use Redis in production)
rate_limit_storage = defaultdict(list)

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Rate limiting decorator
    Args:
        max_requests: Maximum number of requests allowed in the time window
        window_seconds: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            # Get client identifier (IP address)
            client_id = request.client.host

            # Get current time
            now = time()

            # Clean old requests
            rate_limit_storage[client_id] = [
                req_time for req_time in rate_limit_storage[client_id]
                if now - req_time < window_seconds
            ]

            # Check if rate limit exceeded
            if len(rate_limit_storage[client_id]) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds."
                )

            # Add current request
            rate_limit_storage[client_id].append(now)

            # Call the original function
            return await func(*args, request=request, **kwargs)

        return wrapper
    return decorator

# Session management
class SessionManager:
    """Manage user sessions and tokens"""

    def __init__(self):
        self.active_sessions = {}  # In production, use Redis

    def create_session(self, user_id: int, access_token: str, refresh_token: str) -> str:
        """Create a new session"""
        session_id = secrets.token_urlsafe(32)

        self.active_sessions[session_id] = {
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }

        return session_id

    def validate_session(self, session_id: str) -> bool:
        """Check if session is valid"""
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]

        # Check if session expired (30 days)
        if (datetime.utcnow() - session["created_at"]).days > 30:
            self.revoke_session(session_id)
            return False

        # Update last activity
        session["last_activity"] = datetime.utcnow()

        return True

    def revoke_session(self, session_id: str):
        """Revoke a session (logout)"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def revoke_all_user_sessions(self, user_id: int):
        """Revoke all sessions for a user"""
        sessions_to_remove = [
            sid for sid, session in self.active_sessions.items()
            if session["user_id"] == user_id
        ]

        for sid in sessions_to_remove:
            del self.active_sessions[sid]

# Global session manager instance
session_manager = SessionManager()

# Dependency to get database session
def get_db():
    """Database session dependency"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
