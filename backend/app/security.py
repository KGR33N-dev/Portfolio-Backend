"""
Security module for JWT authentication and authorization
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import secrets
import hashlib
import os

from .database import get_db
from .models import User, APIKey, UserRoleEnum
from .datetime_utils import safe_current_time, is_datetime_expired, make_timezone_aware

# Import Response for cookie handling  
from fastapi import Response

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes for access token
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 days for refresh token

# Password hashing with enhanced security
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12,  # Higher rounds for better security
    bcrypt__ident="2b"
)

# JWT Bearer token security
security = HTTPBearer()

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()
IS_DEVELOPMENT = ENVIRONMENT in ["development", "dev", "local"]

# Environment-aware limiter for direct usage
def conditional_limit(rate_string: str):
    """Apply rate limit only in non-development environments"""
    if IS_DEVELOPMENT:
        return lambda func: func  # No-op decorator in development
    return limiter.limit(rate_string)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storing in database"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    """Create a JWT access token with enhanced security"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add additional security claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),  # Issued at
        "jti": secrets.token_urlsafe(16),  # JWT ID for token revocation
        "type": "access"  # Token type
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: int):
    """Create JWT refresh token"""
    data = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": safe_current_time() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": safe_current_time(),
        "jti": secrets.token_urlsafe(16)
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Set HTTP-only cookies for authentication (secure based on environment)"""
    # Check environment to determine if cookies should be secure
    environment = os.getenv("ENVIRONMENT", "production").lower()
    is_secure = environment == "production"  # Only secure in production
    
    # For cross-domain cookies in production, we need specific domain configuration
    domain_config = {}
    if environment == "production":
        # Set domain to allow cookies across subdomains (kgr33n.com and api.kgr33n.com)
        domain_config["domain"] = ".kgr33n.com"
        # Use None for cross-site requests with credentials
        samesite_setting = "none" if is_secure else "lax"
    else:
        samesite_setting = "lax"
    
    # Set access token cookie (15 minutes)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        httponly=True,
        secure=is_secure,  # True for production/HTTPS, False for development/HTTP
        samesite=samesite_setting,
        path="/",
        **domain_config
    )
    
    # Set refresh token cookie (7 days)
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Convert to seconds
        httponly=True,
        secure=is_secure,  # True for production/HTTPS, False for development/HTTP
        samesite=samesite_setting,
        path="/",  # Match the router prefix
        **domain_config
    )

def clear_auth_cookies(response: Response):
    """Clear authentication cookies"""
    # Check environment to determine cookie settings
    environment = os.getenv("ENVIRONMENT", "production").lower()
    is_secure = environment == "production"
    
    # For cross-domain cookies in production, we need specific domain configuration
    domain_config = {}
    if environment == "production":
        domain_config["domain"] = ".kgr33n.com"
        samesite_setting = "none" if is_secure else "lax"
    else:
        samesite_setting = "lax"
    
    response.delete_cookie(
        key="access_token", 
        path="/",
        secure=is_secure,
        httponly=True,
        samesite=samesite_setting,
        **domain_config
    )
    response.delete_cookie(
        key="refresh_token", 
        path="/",
        secure=is_secure,
        httponly=True,
        samesite=samesite_setting,
        **domain_config
    )

def get_token_from_cookie(request: Request, cookie_name: str) -> Optional[str]:
    """Extract token from HTTP-only cookie"""
    return request.cookies.get(cookie_name)

def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify and decode a JWT token with type checking"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
            
        # Check if token is expired using safe datetime comparison
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, timezone.utc) < safe_current_time():
            return None
            
        return payload
    except JWTError:
        return None

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def handle_failed_login(db: Session, email: str) -> None:
    """Handle failed login attempt - increment counter and lock account if needed"""
    user = get_user_by_email(db, email)
    if user:
        # Increment failed login attempts
        if not hasattr(user, 'failed_login_attempts') or user.failed_login_attempts is None:
            user.failed_login_attempts = 1
        else:
            user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if user.failed_login_attempts >= 5:
            user.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        db.commit()

def is_email_valid(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_password_strong(password: str) -> tuple[bool, str]:
    """Check if password meets security requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def authenticate_user(db: Session, email: str, password: str) -> Union[User, bool]:
    """Authenticate user with email and password (email-only authentication)"""
    # Only authenticate by email for better security
    user = get_user_by_email(db, email)
    
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    
    # Check if account is locked
    if hasattr(user, 'account_locked_until') and user.account_locked_until:
        if user.account_locked_until > datetime.now(timezone.utc):
            return False
        else:
            # Unlock account if lock period has expired
            user.account_locked_until = None
            db.commit()
    
    # Reset failed login attempts on successful login
    if hasattr(user, 'failed_login_attempts'):
        user.failed_login_attempts = 0
        user.last_login = datetime.now(timezone.utc)
        db.commit()
    
    return user

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token in cookie"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"translation_code": "INVALID_CREDENTIALS", "message": "Could not validate credentials"},
    )
    
    try:
        # Get token from cookie instead of Authorization header
        token = get_token_from_cookie(request, "access_token")
        if not token:
            raise credentials_exception
            
        payload = verify_token(token, "access")
        if payload is None:
            raise credentials_exception
        
        # Get user by email (sub contains email now, not username)
        user_identifier: str = payload.get("sub")
        if user_identifier is None:
            raise credentials_exception
        
        # Try to get user by email first, fallback to username for backward compatibility
        user = get_user_by_email(db, user_identifier)
        if not user:
            user = get_user_by_username(db, user_identifier)
            
        if user is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail={"translation_code": "INACTIVE_USER", "message": "Inactive user"})
    return current_user

def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user optionally (returns None if no token provided)"""
    token = get_token_from_cookie(request, "access_token")
    if not token:
        return None
    
    try:
        payload = verify_token(token, "access")
        if payload is None:
            return None
        
        user_identifier: str = payload.get("sub")
        if user_identifier is None:
            return None
        
        # Try to get user by email first, fallback to username
        user = get_user_by_email(db, user_identifier)
        if not user:
            user = get_user_by_username(db, user_identifier)
            
        return user if user and user.is_active else None
        
    except JWTError:
        return None

def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current admin user - checks role-based permissions"""
    # Check if user has admin role
    if not current_user.role or current_user.role.name != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"translation_code": "INSUFFICIENT_PERMISSIONS", "message": "Not enough permissions"}
        )
    return current_user

# API Key authentication
def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(db: Session, api_key: str) -> Optional[APIKey]:
    """Verify API key and return the key object if valid"""
    key_hash = hash_api_key(api_key)
    api_key_obj = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()
    
    if api_key_obj and (api_key_obj.expires_at is None or api_key_obj.expires_at > datetime.now(timezone.utc)):
        # Update last used timestamp
        api_key_obj.last_used = datetime.now(timezone.utc)
        db.commit()
        return api_key_obj
    return None

def get_user_from_api_key(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from API key in header"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    api_key_obj = verify_api_key(db, api_key)
    if api_key_obj:
        return api_key_obj.user
    return None

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ):
        # Check if user has admin role (admins have all permissions)
        if current_user.role and current_user.role.name == UserRoleEnum.ADMIN:
            return current_user
        
        # Check user role permissions
        if current_user.role and current_user.role.permissions and permission in current_user.role.permissions:
            return current_user
        
        # Check API key permissions
        api_key = request.headers.get("X-API-Key")
        if api_key:
            api_key_obj = verify_api_key(db, api_key)
            if api_key_obj and permission in api_key_obj.permissions:
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"translation_code": "INSUFFICIENT_PERMISSIONS", "message": f"Permission '{permission}' required"}
        )
    
    return permission_checker

# Rate limiting decorators with enhanced security
def rate_limit_by_key(requests: int = 100, period: int = 3600):
    """Rate limit by API key - disabled in development"""
    if IS_DEVELOPMENT:
        return lambda func: func  # No-op decorator in development
    return limiter.limit(f"{requests}/{period}second")

def rate_limit_by_ip(requests: int = 50, period: int = 3600):
    """Rate limit by IP address - disabled in development"""
    if IS_DEVELOPMENT:
        return lambda func: func  # No-op decorator in development
    return limiter.limit(f"{requests}/{period}second")

def strict_rate_limit_login(requests: int = 5, period: int = 900):
    """Strict rate limiting for login attempts (5 attempts per 15 minutes) - disabled in development"""
    if IS_DEVELOPMENT:
        return lambda func: func  # No-op decorator in development
    return limiter.limit(f"{requests}/{period}second")

def rate_limit_password_reset(requests: int = 3, period: int = 3600):
    """Rate limit password reset requests (3 per hour) - disabled in development"""
    if IS_DEVELOPMENT:
        return lambda func: func  # No-op decorator in development
    return limiter.limit(f"{requests}/{period}second")

# Admin rate limits (more permissive)
def admin_rate_limit(requests: int = 1000, period: int = 3600):
    """Higher rate limits for admin operations - disabled in development"""
    if IS_DEVELOPMENT:
        return lambda func: func  # No-op decorator in development
    return limiter.limit(f"{requests}/{period}second")

# Security headers and CSRF protection
def get_security_headers() -> dict:
    """Get recommended security headers"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

def generate_csrf_token() -> str:
    """Generate CSRF token for form protection"""
    return secrets.token_urlsafe(32)

def verify_csrf_token(token: str, session_token: str) -> bool:
    """Verify CSRF token"""
    return secrets.compare_digest(token, session_token)

# Session management
def create_session_token() -> str:
    """Create secure session token"""
    return secrets.token_urlsafe(64)

def hash_session_token(token: str) -> str:
    """Hash session token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()

# Email verification system
def generate_verification_code() -> str:
    """Generate 6-digit verification code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def generate_verification_token() -> str:
    """Generate secure verification token"""
    return secrets.token_urlsafe(32)

def create_verification_token(email: str, verification_code: str) -> str:
    """Create JWT token for email verification"""
    data = {
        "email": email,
        "code": verification_code,
        "type": "email_verification",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),  # 15 minutes expiry
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(16)
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_verification_token(token: str) -> Optional[dict]:
    """Verify email verification token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != "email_verification":
            return None
            
        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            return None
            
        return payload
    except JWTError:
        return None

def hash_verification_code(code: str) -> str:
    """Hash verification code for storage using bcrypt (secure)"""
    return pwd_context.hash(code)

def verify_verification_code(plain_code: str, hashed_code: str) -> bool:
    """Verify verification code against bcrypt hash"""
    try:
        return pwd_context.verify(plain_code, hashed_code)
    except Exception:
        return False

# Email sending functionality using Resend
async def send_verification_email(email: str, verification_code: str, verification_token: str) -> bool:
    """Send verification email to user using Resend"""
    try:
        from .email_service import EmailService
        
        # Get username from email (fallback)
        username = email.split('@')[0]
        
        # Try to get actual username from database
        from .database import SessionLocal
        from .models import User
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if user:
                username = user.username or user.full_name or username
        finally:
            db.close()
        
        result = await EmailService.send_verification_email(email, verification_code, username)
        
        if result["success"]:
            print(f"✅ Verification email sent to {email}")
            return True
        else:
            print(f"❌ Failed to send verification email to {email}: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send verification email: {e}")
        # Fallback: log the code for development
        print(f"🔐 Verification code for {email}: {verification_code}")
        print(f"🔗 Verification token: {verification_token}")
        return False

async def send_password_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email using Resend"""
    try:
        from .email_service import EmailService
        
        # Get username from email (fallback)
        username = email.split('@')[0]
        
        # Try to get actual username from database
        from .database import SessionLocal
        from .models import User
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if user:
                username = user.username or user.full_name or username
        finally:
            db.close()
        
        result = await EmailService.send_password_reset_email(email, reset_token, username)
        
        if result["success"]:
            print(f"✅ Password reset email sent to {email}")
            return True
        else:
            print(f"❌ Failed to send password reset email to {email}: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send password reset email: {e}")
        # Fallback: log the token for development
        print(f"🔐 Password reset token for {email}: {reset_token}")
        return False
