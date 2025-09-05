"""
Router dla zarządzania systemem ról i rang użytkowników
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..database import get_db
from ..models import User, UserRole, UserRank, UserRoleEnum, UserRankEnum
from ..schemas import UserRole as UserRoleSchema, UserRank as UserRankSchema, UserWithRoleRank
from ..security import get_current_user, get_current_admin_user
from ..rank_utils import auto_check_rank_upgrade

router = APIRouter(prefix="/api/roles", tags=["User Roles & Ranks"])

# 🎯 ROLE MANAGEMENT ENDPOINTS

@router.get("/roles", response_model=List[UserRoleSchema])
def get_all_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pobierz wszystkie dostępne role"""
    roles = db.query(UserRole).filter(UserRole.is_active == True).all()
    return roles

@router.get("/ranks", response_model=List[UserRankSchema])
def get_all_ranks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pobierz wszystkie dostępne rangi"""
    ranks = db.query(UserRank).filter(UserRank.is_active == True).order_by(UserRank.level).all()
    return ranks

@router.get("/user/{user_id}", response_model=UserWithRoleRank)
def get_user_role_rank(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pobierz informacje o roli i randze użytkownika"""
    user = db.query(User).options(
        joinedload(User.role),
        joinedload(User.rank)
    ).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "USER_NOT_FOUND", "message": "User not found"}
        )
    
    # Tylko admin lub sam użytkownik może zobaczyć szczegóły
    if current_user.id != user.id and not current_user.has_permission("user.manage"):
        raise HTTPException(
            status_code=403, 
            detail={"translation_code": "INSUFFICIENT_PERMISSIONS", "message": "Not enough permissions"}
        )
    
    # Dodaj computed fields
    user_data = UserWithRoleRank.from_orm(user)
    user_data.display_role = user.get_display_role()
    user_data.display_rank = user.get_display_rank()
    user_data.role_color = user.get_role_color()
    user_data.rank_icon = user.get_rank_icon()
    
    return user_data

@router.post("/user/{user_id}/role/{role_name}")
def assign_user_role(
    user_id: int,
    role_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Przypisz rolę użytkownikowi (tylko admin)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "USER_NOT_FOUND", "message": "User not found"}
        )
    
    role = db.query(UserRole).filter(UserRole.name == role_name).first()
    if not role:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "ROLE_NOT_FOUND", "message": "Role not found"}
        )
    
    user.role_id = role.id
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Przypisano rolę {role.display_name} użytkownikowi {user.username}"
    }

@router.post("/user/{user_id}/rank/{rank_name}")
def assign_user_rank(
    user_id: int,
    rank_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Przypisz rangę użytkownikowi (tylko admin)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "USER_NOT_FOUND", "message": "User not found"}
        )
    
    rank = db.query(UserRank).filter(UserRank.name == rank_name).first()
    if not rank:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "RANK_NOT_FOUND", "message": "Rank not found"}
        )
    
    user.rank_id = rank.id
    db.commit()
    
    return {
        "success": True,
        "message": f"Przypisano rangę {rank.display_name} użytkownikowi {user.username}"
    }

@router.post("/check-rank-upgrade/{user_id}")
def check_rank_upgrade(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sprawdź i automatycznie awansuj rangę użytkownika (manualnie)"""
    
    # Sprawdź uprawnienia
    if current_user.id != user_id and not current_user.has_permission("user.manage"):
        raise HTTPException(
            status_code=403, 
            detail={"translation_code": "INSUFFICIENT_PERMISSIONS", "message": "Not enough permissions"}
        )
    
    # Użyj funkcji pomocniczej
    result = auto_check_rank_upgrade(user_id, db)
    
    if not result["success"]:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "USER_NOT_FOUND", "message": result["message"]}
        )
    
    return result

# 🎯 UTILITY ENDPOINTS

@router.get("/permissions")
def get_available_permissions(
    current_user: User = Depends(get_current_admin_user)
):
    """Lista wszystkich dostępnych uprawnień w systemie"""
    return {
        "permissions": [
            "comment.create", "comment.like", "comment.moderate", "comment.delete",
            "post.create", "post.edit", "post.delete", "post.publish",
            "user.manage", "role.manage", "system.admin",
            "profile.edit", "profile.view"
        ],
        "roles": list(UserRoleEnum),
        "ranks": list(UserRankEnum)
    }

@router.get("/my-profile", response_model=UserWithRoleRank)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pobierz własny profil z rolą i rangą"""
    user = db.query(User).options(
        joinedload(User.role),
        joinedload(User.rank)
    ).filter(User.id == current_user.id).first()
    
    user_data = UserWithRoleRank.from_orm(user)
    user_data.display_role = user.get_display_role()
    user_data.display_rank = user.get_display_rank()
    user_data.role_color = user.get_role_color()
    user_data.rank_icon = user.get_rank_icon()
    
    return user_data
