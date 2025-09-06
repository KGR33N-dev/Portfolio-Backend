"""
Authentication router with email verification system
"""
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..datetime_utils import safe_datetime_comparison, is_datetime_expired, safe_current_time
from ..models import User, APIKey, UserRole, UserRank, UserRoleEnum, UserRankEnum
from ..schemas import (
    UserCreate, UserLogin, UserResponse, AuthResponse, User as UserSchema, UserWithRoleRank,
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
    hash_verification_code, verify_verification_code, set_auth_cookies, clear_auth_cookies
)
from ..email_service import EmailService

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
            detail={"translation_code": "INVALID_EMAIL_FORMAT", "message": "Invalid email format"}
        )
    
    # Validate password strength
    is_strong, message = is_password_strong(user_data.password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "WEAK_PASSWORD", "message": message}
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
                    detail={"translation_code": "EMAIL_EXISTS", "message": "User with this email already exists and is verified"}
                )
            else:
                # Resend verification code for unverified user
                verification_code = generate_verification_code()
                verification_token = create_verification_token(user_data.email, verification_code)
                
                # Update existing user with new verification data
                existing_user.verification_code_hash = hash_verification_code(verification_code)
                existing_user.verification_token = verification_token
                existing_user.verification_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
                
                db.commit()
                
                # Send verification email with user's language preference
                email_service = EmailService()
                # Use language from request body if provided, otherwise fallback to headers
                user_language = user_data.language if user_data.language in ["pl", "en"] else email_service.get_user_language_from_request(request)
                email_result = await email_service.send_verification_email(
                    user_data.email, verification_code, existing_user.username, user_language
                )
                
                if not email_result.get("success", False):
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail={"translation_code": "EMAIL_SEND_FAILED", "message": "Failed to send verification email"}
                    )
                
                return APIResponse(
                    success=True,
                    message="Verification code resent to your email address",
                    type="success",
                    translation_code="VERIFICATION_CODE_SENT",
                    data={"email": user_data.email, "expires_in_minutes": 15}
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"translation_code": "USERNAME_EXISTS", "message": "User with this username already exists"}
            )
    
    # Generate verification code and token
    verification_code = generate_verification_code()
    verification_token = create_verification_token(user_data.email, verification_code)
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Get default role and rank for new users
    default_role = db.query(UserRole).filter(UserRole.name == UserRoleEnum.USER).first()
    default_rank = db.query(UserRank).filter(UserRank.name == UserRankEnum.NEWBIE).first()
    
    if not default_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"translation_code": "SERVER_CONFIG_ERROR", "message": "Default user role not found. Please contact administrator."}
        )
    
    if not default_rank:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"translation_code": "SERVER_CONFIG_ERROR", "message": "Default user rank not found. Please contact administrator."}
        )
    
    # Create new unverified user with role-based system
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        bio=user_data.bio,
        is_active=False,  # Inactive until email verified
        role_id=default_role.id,  # Assign default role
        rank_id=default_rank.id,  # Assign default rank
        email_verified=False,
        verification_code_hash=hash_verification_code(verification_code),
        verification_token=verification_token,
        verification_expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        account_expires_at=datetime.now(timezone.utc) + timedelta(days=1)  # Account expires in 24 hours if not verified
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email using EmailService with user's language preference
    email_service = EmailService()
    # Use language from request body if provided, otherwise fallback to headers
    user_language = user_data.language if user_data.language in ["pl", "en"] else email_service.get_user_language_from_request(request)
    email_result = await email_service.send_verification_email(
        user_data.email, verification_code, user_data.username, user_language
    )
    
    if not email_result.get("success", False):
        # Rollback user creation if email failed
        db.delete(db_user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"translation_code": "EMAIL_SEND_FAILED", "message": "Failed to send verification email"}
        )
    
    return APIResponse(
        success=True,
        type="success",
        translation_code="REGISTRATION_SUCCESS",
        message="Registration successful! Check your email for verification code",
        data={
            "email": user_data.email,
            "expires_in_minutes": 15,
            "user_id": db_user.id
        }
    )

@router.post("/verify-email", response_model=AuthResponse)
@rate_limit_by_ip(requests=10, period=3600)  # 10 verification attempts per hour
async def verify_email(
    verification_data: EmailVerificationConfirm,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Verify email with 6-digit code"""
    # Find user by email
    user = db.query(User).filter(User.email == verification_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"translation_code": "USER_NOT_FOUND", "message": "User not found"}
        )
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "EMAIL_ALREADY_VERIFIED", "message": "Email already verified"}
        )
    
    # Check if verification code is expired
    if not user.verification_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "VERIFICATION_CODE_EXPIRED", "message": "Verification code expired. Please request a new one."}
        )
    
    # Handle timezone comparison safely
    current_time = datetime.now(timezone.utc)
    expires_at = user.verification_expires_at
    
    # If database datetime is naive, make it timezone-aware
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < current_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "VERIFICATION_CODE_EXPIRED", "message": "Verification code expired. Please request a new one."}
        )
    
    # Verify the code
    if not user.verification_code_hash or not verify_verification_code(
        verification_data.verification_code, 
        user.verification_code_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "INVALID_VERIFICATION_CODE", "message": "Invalid verification code"}
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
    access_token_expires = timedelta(minutes=15)  # Changed to 15 minutes
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(user.id)
    
    # Set HTTP-only cookies (secure based on environment)
    set_auth_cookies(response, access_token, refresh_token)
    
    return AuthResponse(
        user=UserSchema.from_orm(user),
        message="Email verified successfully"
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
            type="info",
            translation_code="VERIFICATION_CODE_RESENT",
            message="If the email exists, a new verification code has been sent",
            data={"expires_in_minutes": 15}
        )
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "EMAIL_ALREADY_VERIFIED","type":"info", "message": "Email already verified"}
        )
    
    # Generate new verification code
    verification_code = generate_verification_code()
    verification_token = create_verification_token(email_data.email, verification_code)
    
    # Update user verification data
    user.verification_code_hash = hash_verification_code(verification_code)
    user.verification_token = verification_token
    user.verification_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    db.commit()
    
    # Send verification email using EmailService with user's language preference
    email_service = EmailService()
    # Use language from request body if provided, otherwise fallback to headers
    user_language = email_data.language if email_data.language in ["pl", "en"] else email_service.get_user_language_from_request(request)
    email_result = await email_service.send_verification_email(
        email_data.email, verification_code, user.username, user_language
    )
    
    if not email_result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"translation_code": "EMAIL_SEND_FAILED", "message": "Failed to send verification email"}
        )
    
    return APIResponse(
        success=True,
        type="info",
        translation_code="VERIFICATION_CODE_RESENT",
        message="New verification code sent to your email",
        data={"expires_in_minutes": 15}
    )

@router.post("/login", response_model=AuthResponse)
async def login_user(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user with email and password (email-only authentication)"""
    # Try to authenticate with email only
    user = authenticate_user(db, form_data.username, form_data.password)  # username field contains email
    
    if not user:
        # Handle failed login attempt
        handle_failed_login(db, form_data.username)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"translation_code": "INVALID_CREDENTIALS", "message": "Incorrect email or password"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "ACCOUNT_NOT_ACTIVATED", "message": "Account not activated. Please verify your email first."}
        )
    
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "EMAIL_NOT_VERIFIED", "message": "Email not verified. Please check your email for verification code."}
        )
    
    # Check if account is locked
    if hasattr(user, 'account_locked_until') and user.account_locked_until:
        current_time = datetime.now(timezone.utc)
        if user.account_locked_until.tzinfo is None:
            current_time = datetime.now()
        
        if user.account_locked_until > current_time:
            lock_time_remaining = user.account_locked_until - current_time
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={"translation_code": "ACCOUNT_LOCKED", "message": f"Account locked. Try again in {lock_time_remaining.seconds // 60} minutes."}
            )
    
    access_token_expires = timedelta(minutes=15)  # Changed to 15 minutes
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires  # Use email as subject
    )
    
    refresh_token = create_refresh_token(user.id)
    
    # Set HTTP-only cookies (secure based on environment)
    set_auth_cookies(response, access_token, refresh_token)
    
    return AuthResponse(
        user=UserSchema.from_orm(user),
        message="Login successful"
    )

@router.get("/me", response_model=UserWithRoleRank)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user information with role and rank details"""
    # Fetch user with role and rank relationships
    user_with_relations = db.query(User).options(
        joinedload(User.role),
        joinedload(User.rank)
    ).filter(User.id == current_user.id).first()
    
    return UserWithRoleRank.from_orm(user_with_relations)

@router.post("/logout", response_model=APIResponse)
async def logout_user(
    response: Response
):
    """Logout user by clearing authentication cookies"""
    clear_auth_cookies(response)
    
    return APIResponse(
        success=True,
        type="success",
        translation_code="LOGOUT_SUCCESS",
        message="Logged out successfully",
        data={}
    )

@router.post("/refresh", response_model=APIResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token from cookie"""
    from ..security import get_token_from_cookie, verify_token
    
    refresh_token = get_token_from_cookie(request, "refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"translation_code": "NO_REFRESH_TOKEN", "message": "No refresh token provided"}
        )
    
    # Verify refresh token
    payload = verify_token(refresh_token, "refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"translation_code": "INVALID_REFRESH_TOKEN", "message": "Invalid refresh token"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"translation_code": "INVALID_REFRESH_TOKEN", "message": "Invalid refresh token"}
        )
    
    # Get user by ID
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"translation_code": "USER_NOT_FOUND", "message": "User not found or inactive"}
        )
    
    # Create new access token
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=timedelta(minutes=15)
    )
    
    # Create new refresh token for security (token rotation)
    new_refresh_token = create_refresh_token(user.id)
    
    # Set both tokens as cookies (using environment-based security)
    set_auth_cookies(response, access_token, new_refresh_token)
    
    return APIResponse(
        success=True,
        type="success", 
        translation_code="TOKEN_REFRESHED",
        message="Access token refreshed successfully",
        data={}
    )

@router.post("/password-reset-request", response_model=APIResponse)
@rate_limit_by_ip(requests=3, period=3600)  # 3 password reset requests per hour
async def request_password_reset(
    reset_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Request password reset - sends reset token to email"""
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    if not user:
        # Return error if user doesn't exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"translation_code": "USER_NOT_FOUND", "message": "No account found with this email address"}
        )
    
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "EMAIL_NOT_VERIFIED", "message": "Email not verified. Cannot reset password for unverified account."}
        )
    
    # Generate password reset token
    reset_token = generate_verification_token()
    
    # Update user with reset token
    user.password_reset_token = reset_token
    user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    db.commit()
    
    # Send password reset email using EmailService with user's language preference
    email_service = EmailService()
    # Use language from request body if provided, otherwise fallback to headers
    user_language = reset_data.language if reset_data.language in ["pl", "en"] else email_service.get_user_language_from_request(request)
    email_result = await email_service.send_password_reset_email(
        reset_data.email, reset_token, user.username, user_language
    )
    
    if not email_result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"translation_code": "EMAIL_SEND_FAILED", "message": "Failed to send password reset email"}
        )
    
    return APIResponse(
        success=True,
        notification_type="success",
        translation_code="PASSWORD_RESET_REQUEST_SUCCESS",
        message="Password reset email has been sent successfully",
        data={
            "expires_in_minutes": 30,
            "email_sent": True,
            "email_address": reset_data.email
        }
    )

@router.post("/password-reset-confirm", response_model=APIResponse)
@rate_limit_by_ip(requests=5, period=3600)  # 5 password reset confirmations per hour
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"translation_code": "USER_NOT_FOUND", "message": "User not found"}
        )
    
    # Check if reset token is valid and not expired
    current_time = datetime.now(timezone.utc)
    if user.password_reset_expires_at and user.password_reset_expires_at.tzinfo is None:
        # If database datetime is naive, use naive current time for comparison
        current_time = datetime.now()
    
    if (not user.password_reset_token or 
        not user.password_reset_expires_at or 
        user.password_reset_expires_at < current_time or
        user.password_reset_token != reset_data.reset_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "INVALID_RESET_TOKEN", "message": "Invalid or expired reset token"}
        )
    
    # Validate new password strength
    is_strong, message = is_password_strong(reset_data.new_password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "WEAK_PASSWORD", "message": message}
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    user.failed_login_attempts = 0  # Reset failed attempts
    user.account_locked_until = None  # Unlock account if locked
    
    db.commit()
    
    return APIResponse(
        success=True,
        type="success",
        translation_code="PASSWORD_RESET_SUCCESS",
        message="Password reset successful. You can now login with your new password.",
        data={}
    )

# API Key endpoints remain the same
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
        expires_at = datetime.now(timezone.utc) + timedelta(days=api_key_data.expires_days)
    
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
            detail={"translation_code": "API_KEY_NOT_FOUND", "message": "API key not found"}
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
            detail={"translation_code": "API_KEY_NOT_FOUND", "message": "API key not found"}
        )
    
    api_key.is_active = not api_key.is_active
    db.commit()
    
    return {
        "message": f"API key {'activated' if api_key.is_active else 'deactivated'}",
        "is_active": api_key.is_active
    }
