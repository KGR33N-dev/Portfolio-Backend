"""
User profile management router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import User, UserRoleEnum, Comment, CommentLike, APIKey
from ..schemas import APIResponse
from ..security import (
    get_current_user, verify_password, get_password_hash, 
    is_password_strong, is_email_valid
)
from pydantic import BaseModel, Field

router = APIRouter(prefix="/profile", tags=["user profile"])

# Schemas for profile operations
class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

class ChangeUsernameRequest(BaseModel):
    new_username: str = Field(..., min_length=3, max_length=50)
    current_password: str = Field(..., min_length=1)

class ChangeEmailRequest(BaseModel):
    new_email: str = Field(..., min_length=5, max_length=255)
    current_password: str = Field(..., min_length=1)

class DeleteAccountRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    confirmation: str = Field(..., pattern="^DELETE_MY_ACCOUNT$")

@router.put("/change-password", response_model=APIResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Zmień hasło użytkownika (wymaga obecnego hasła)"""
    
    # Sprawdź czy nowe hasła się zgadzają
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "PASSWORD_MISMATCH", "message": "Nowe hasła nie są identyczne"}
        )
    
    # Sprawdź obecne hasło
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "INVALID_CURRENT_PASSWORD", "message": "Nieprawidłowe obecne hasło"}
        )
    
    # Sprawdź czy nowe hasło nie jest takie same jak obecne
    if verify_password(request.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "SAME_PASSWORD", "message": "Nowe hasło musi być różne od obecnego"}
        )
    
    # Sprawdź siłę nowego hasła
    is_strong, message = is_password_strong(request.new_password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "WEAK_PASSWORD", "message": f"Hasło jest za słabe: {message}"}
        )
    
    # Zaktualizuj hasło
    current_user.hashed_password = get_password_hash(request.new_password)
    current_user.failed_login_attempts = 0  # Resetuj nieudane próby
    current_user.account_locked_until = None  # Odblokuj konto jeśli było zablokowane
    
    db.commit()
    
    return APIResponse(
        success=True,
        type="success",
        translation_code="PASSWORD_CHANGED",
        message="Hasło zostało pomyślnie zmienione"
    )

@router.put("/change-username", response_model=APIResponse)
async def change_username(
    request: ChangeUsernameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Zmień username/nick użytkownika (wymaga hasła + weryfikacja unikalności)"""
    
    # Sprawdź obecne hasło
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "INVALID_CURRENT_PASSWORD", "message": "Nieprawidłowe hasło"}
        )
    
    # Sprawdź czy nowy username nie jest taki sam jak obecny
    if request.new_username.lower() == current_user.username.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "SAME_USERNAME", "message": "Nowy username musi być różny od obecnego"}
        )
    
    # 🔍 WERYFIKACJA UNIKALNOŚCI USERNAME
    existing_user = db.query(User).filter(
        User.username.ilike(request.new_username),  # Case-insensitive check
        User.id != current_user.id  # Exclude current user
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "USERNAME_EXISTS", "message": "Ten username jest już zajęty"}
        )
    
    # Sprawdź format username (tylko litery, cyfry, podkreślniki, myślniki)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', request.new_username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "INVALID_USERNAME_FORMAT", "message": "Username może zawierać tylko litery, cyfry, podkreślniki i myślniki"}
        )
    
    # Zaktualizuj username
    old_username = current_user.username
    current_user.username = request.new_username
    
    db.commit()
    
    return APIResponse(
        success=True,
        type="success",
        translation_code="USERNAME_CHANGED",
        message=f"Username został zmieniony z '{old_username}' na '{request.new_username}'"
    )

@router.put("/change-email", response_model=APIResponse)
async def change_email(
    request: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Zmień email użytkownika (wymaga hasła + weryfikacja unikalności)"""
    
    # Sprawdź obecne hasło
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "INVALID_CURRENT_PASSWORD", "message": "Nieprawidłowe hasło"}
        )
    
    # Sprawdź format email
    if not is_email_valid(request.new_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "INVALID_EMAIL_FORMAT", "message": "Nieprawidłowy format email"}
        )
    
    # Sprawdź czy nowy email nie jest taki sam jak obecny
    if request.new_email.lower() == current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "SAME_EMAIL", "message": "Nowy email musi być różny od obecnego"}
        )
    
    # 🔍 WERYFIKACJA UNIKALNOŚCI EMAIL
    existing_user = db.query(User).filter(
        User.email.ilike(request.new_email),  # Case-insensitive check
        User.id != current_user.id  # Exclude current user
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "EMAIL_EXISTS", "message": "Ten email jest już używany przez inne konto"}
        )
    
    # Zaktualizuj email i ustaw jako niezweryfikowany
    old_email = current_user.email
    current_user.email = request.new_email
    current_user.email_verified = False  # Wymag ponownej weryfikacji
    current_user.verification_token = None
    current_user.verification_expires_at = None
    
    db.commit()
    
    return APIResponse(
        success=True,
        type="success",
        translation_code="EMAIL_CHANGED",
        message=f"Email został zmieniony z '{old_email}' na '{request.new_email}'. Wymagana jest ponowna weryfikacja.",
        data={"requires_verification": True}
    )

@router.delete("/delete-account", response_model=APIResponse)
async def delete_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🚨 USUŃ KONTO UŻYTKOWNIKA (nieodwracalne!)
    Wymaga hasła + potwierdzenia "DELETE_MY_ACCOUNT"
    """
    
    # Sprawdź obecne hasło
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "INVALID_CURRENT_PASSWORD", "message": "Nieprawidłowe hasło"}
        )
    
    # Sprawdź potwierdzenie
    if request.confirmation != "DELETE_MY_ACCOUNT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "INVALID_CONFIRMATION", "message": "Nieprawidłowe potwierdzenie. Wpisz dokładnie: DELETE_MY_ACCOUNT"}
        )
    
    # Dodatkowa ochrona - nie pozwól usunąć konta administratora
    if current_user.role and current_user.role.name == UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"translation_code": "ADMIN_DELETE_FORBIDDEN", "message": "Nie można usunąć konta administratora. Skontaktuj się z innym administratorem."}
        )
    
    # Zapisz informacje przed usunięciem (dla logów)
    deleted_username = current_user.username
    deleted_email = current_user.email
    deleted_id = current_user.id
    
    try:
        # 🗑️ USUNIĘCIE KONTA
        # Najpierw usuwamy powiązane dane ręcznie, aby uniknąć problemów z foreign key constraints
        
        # 1. Usuń polubienia komentarzy użytkownika
        db.query(CommentLike).filter(CommentLike.user_id == current_user.id).delete()
        
        # 2. Usuń komentarze użytkownika (wraz z odpowiedziami dzięki CASCADE w parent_id)
        db.query(Comment).filter(Comment.user_id == current_user.id).delete()
        
        # 3. Usuń klucze API użytkownika
        db.query(APIKey).filter(APIKey.user_id == current_user.id).delete()
        
        # 4. Usuń użytkownika
        db.delete(current_user)
        db.commit()
        
        # Log usunięcia konta (opcjonalnie można zapisać do tabeli audytu)
        print(f"🗑️ KONTO USUNIĘTE: ID={deleted_id}, username={deleted_username}, email={deleted_email}")
        
        return APIResponse(
            success=True,
            type="success",
            translation_code="ACCOUNT_DELETED",
            message=f"Konto '{deleted_username}' zostało permanentnie usunięte. Dziękujemy za korzystanie z naszej platformy."
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"translation_code": "ACCOUNT_DELETE_ERROR", "message": "Wystąpił błąd podczas usuwania konta. Spróbuj ponownie lub skontaktuj się z pomocą techniczną."}
        )

@router.get("/", response_model=dict)
async def get_profile_info(
    current_user: User = Depends(get_current_user)
):
    """Pobierz podstawowe informacje o profilu użytkownika"""
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.email_verified,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login,
        "total_comments": current_user.total_comments,
        "total_likes_received": current_user.total_likes_received,
        "role": {
            "id": current_user.role.id if current_user.role else None,
            "name": current_user.role.name if current_user.role else None,
            "display_name": current_user.role.display_name if current_user.role else None,
            "color": current_user.role.color if current_user.role else None,
        } if current_user.role else None,
        "rank": {
            "id": current_user.rank.id if current_user.rank else None,
            "name": current_user.rank.name if current_user.rank else None,
            "display_name": current_user.rank.display_name if current_user.rank else None,
            "color": current_user.rank.color if current_user.rank else None,
            "icon": current_user.rank.icon if current_user.rank else None,
            "level": current_user.rank.level if current_user.rank else None,
        } if current_user.rank else None,
        "account_status": {
            "is_locked": current_user.account_locked_until is not None,
            "locked_until": current_user.account_locked_until,
            "failed_attempts": current_user.failed_login_attempts
        }
    }
