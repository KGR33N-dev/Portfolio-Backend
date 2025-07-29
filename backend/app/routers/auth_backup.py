"""
Authentication router for user login, registration, and token management
"""
from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, APIKey
from ..schemas import (
    UserCreate, UserLogin, UserResponse, Token, User as UserSchema,
    APIKeyCreate, APIKeyResponse, APIKey as APIKeySchema, APIResponse,
    EmailVerificationRequest, EmailVerificationConfirm, PasswordResetRequest,
    PasswordResetConfirm, UserRegistrationRequest
)
from ..security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    authenticate_user, get_current_active_user, get_current_admin_user,
    generate_api_key, hash_api_key, rate_limit_by_ip, admin_rate_limit,
    strict_rate_limit_login, handle_failed_login, is_email_valid, 
    is_password_strong, get_security_headers, generate_verification_code,
    generate_verification_token, create_verification_token, verify_verification_token,
    hash_verification_code, verify_verification_code, send_verification_email,
    send_password_reset_email
)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=APIResponse)
@rate_limit_by_ip(requests=3, period=3600)  # 3 registrations per hour per IP
async def register_user(
    user_data: UserRegistrationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user - sends verification email"""
    # Validate email format
    if not is_email_valid(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Validate password strength
    is_strong, message = is_password_strong(user_data.password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Check if user already exists (email or username)
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            if existing_user.email_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists and is verified"
                )
            else:
                # Resend verification code for unverified user
                verification_code = generate_verification_code()
                verification_token = create_verification_token(user_data.email, verification_code)
                
                # Update existing user with new verification data
                existing_user.verification_code_hash = hash_verification_code(verification_code)
                existing_user.verification_token = verification_token
                existing_user.verification_expires_at = datetime.utcnow() + timedelta(minutes=15)
                
                db.commit()
                
                # Send verification email
                email_sent = await send_verification_email(user_data.email, verification_code, verification_token)
                
                if not email_sent:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to send verification email"
                    )
                
                return APIResponse(
                    success=True,
                    message="Verification code resent to your email address",
                    data={"email": user_data.email, "expires_in_minutes": 15}
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists"
            )
    
    # Generate verification code and token
    verification_code = generate_verification_code()
    verification_token = create_verification_token(user_data.email, verification_code)
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create new unverified user
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        bio=user_data.bio,
        is_active=False,  # Inactive until email verified
        is_admin=False,
        email_verified=False,
        verification_code_hash=hash_verification_code(verification_code),
        verification_token=verification_token,
        verification_expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    email_sent = await send_verification_email(user_data.email, verification_code, verification_token)
    
    if not email_sent:
        # Rollback user creation if email failed
        db.delete(db_user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return APIResponse(
        success=True,
        message="Registration successful! Check your email for verification code",
        data={
            "email": user_data.email,
            "expires_in_minutes": 15,
            "user_id": db_user.id
        }
    )

@router.post("/verify-email", response_model=UserResponse)
@rate_limit_by_ip(requests=10, period=3600)  # 10 verification attempts per hour
async def verify_email(
    verification_data: EmailVerificationConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify email with 6-digit code"""
    # Find user by email
    user = db.query(User).filter(User.email == verification_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Check if verification code is expired
    if not user.verification_expires_at or user.verification_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Please request a new one."
        )
    
    # Verify the code
    if not user.verification_code_hash or not verify_verification_code(
        verification_data.verification_code, 
        user.verification_code_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Activate user account
    user.email_verified = True
    user.is_active = True
    user.verification_code_hash = None
    user.verification_token = None
    user.verification_expires_at = None
    
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(user.id)
    
    return UserResponse(
        user=UserSchema.from_orm(user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.post("/resend-verification", response_model=APIResponse)
@rate_limit_by_ip(requests=3, period=3600)  # 3 resend attempts per hour
async def resend_verification_code(
    email_data: EmailVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Resend verification code to email"""
    user = db.query(User).filter(User.email == email_data.email).first()
    
    if not user:
        # Don't reveal if user exists or not for security
        return APIResponse(
            success=True,
            message="If the email exists, a new verification code has been sent",
            data={"expires_in_minutes": 15}
        )
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new verification code
    verification_code = generate_verification_code()
    verification_token = create_verification_token(email_data.email, verification_code)
    
    # Update user verification data
    user.verification_code_hash = hash_verification_code(verification_code)
    user.verification_token = verification_token
    user.verification_expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    db.commit()
    
    # Send verification email
    email_sent = await send_verification_email(email_data.email, verification_code, verification_token)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return APIResponse(
        success=True,
        message="New verification code sent to your email",
        data={"expires_in_minutes": 15}
    )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        bio=user_data.bio,
        is_active=True,
        is_admin=False  # First user can be manually promoted to admin
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token with email as subject
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    return UserResponse(
        user=UserSchema.from_orm(db_user),
        access_token=access_token,
        token_type="bearer"
    )

@router.post("/login", response_model=Token)
@strict_rate_limit_login()
async def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user with email and password (email-only authentication)"""
    # Validate email format
    if not is_email_valid(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address"
        )
    
    # Try to authenticate with email only
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        # Handle failed login attempt
        handle_failed_login(db, form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated. Please contact support."
        )
    
    # Create tokens with email as subject
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes in seconds
        user=UserSchema.from_orm(user)
    )

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserSchema.from_orm(current_user)

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new API key (admin only)"""
    # Generate API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_preview = api_key[:8] + "..."
    
    # Calculate expiration
    expires_at = None
    if api_key_data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_days)
    
    # Create API key record
    db_api_key = APIKey(
        name=api_key_data.name,
        key_hash=key_hash,
        key_preview=key_preview,
        permissions=api_key_data.permissions,
        user_id=current_user.id,
        expires_at=expires_at
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return APIKeyResponse(
        api_key=APIKeySchema.from_orm(db_api_key),
        full_key=api_key
    )

@router.get("/api-keys", response_model=list[APIKeySchema])
async def list_api_keys(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all API keys for current admin user"""
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    return [APIKeySchema.from_orm(key) for key in api_keys]

@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete an API key (admin only)"""
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API key deleted successfully"}

@router.patch("/api-keys/{api_key_id}/toggle")
async def toggle_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Toggle API key active status"""
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_active = not api_key.is_active
    db.commit()
    
    return {
        "message": f"API key {'activated' if api_key.is_active else 'deactivated'}",
        "is_active": api_key.is_active
    }
