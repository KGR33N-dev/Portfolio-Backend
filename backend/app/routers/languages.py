"""
Language management router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Language, User
from ..schemas import LanguageCreate, LanguageUpdate, Language as LanguageSchema, APIResponse
from ..security import get_current_admin_user

router = APIRouter()

@router.get("/", response_model=List[LanguageSchema])
async def get_languages(
    db: Session = Depends(get_db),
    active_only: bool = Query(True, description="Show only active languages")
):
    """Pobierz listę wszystkich języków"""
    query = db.query(Language)
    
    if active_only:
        query = query.filter(Language.is_active == True)
    
    languages = query.order_by(Language.name).all()
    return languages

@router.get("/codes", response_model=List[str])
async def get_language_codes(
    db: Session = Depends(get_db),
    active_only: bool = Query(True, description="Show only active language codes")
):
    """Pobierz listę kodów języków (dla walidacji)"""
    query = db.query(Language.code)
    
    if active_only:
        query = query.filter(Language.is_active == True)
    
    codes = query.all()
    return [code[0] for code in codes]

@router.get("/{language_code}", response_model=LanguageSchema)
async def get_language(
    language_code: str,
    db: Session = Depends(get_db)
):
    """Pobierz szczegóły konkretnego języka"""
    language = db.query(Language).filter(Language.code == language_code).first()
    
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"translation_code": "LANGUAGE_NOT_FOUND", "message": f"Language with code '{language_code}' not found"}
        )
    
    return language

@router.post("/", response_model=LanguageSchema, status_code=status.HTTP_201_CREATED)
async def create_language(
    language_data: LanguageCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Dodaj nowy język (admin only)"""
    
    # Check if language code already exists
    existing_language = db.query(Language).filter(Language.code == language_data.code.lower()).first()
    if existing_language:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "LANGUAGE_EXISTS", "message": f"Language with code '{language_data.code}' already exists"}
        )
    
    # Create new language
    new_language = Language(
        code=language_data.code.lower(),
        name=language_data.name,
        native_name=language_data.native_name,
        created_by=current_user.id
    )
    
    db.add(new_language)
    db.commit()
    db.refresh(new_language)
    
    return new_language

@router.put("/{language_code}", response_model=LanguageSchema)
async def update_language(
    language_code: str,
    language_data: LanguageUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Aktualizuj język (admin only)"""
    
    language = db.query(Language).filter(Language.code == language_code).first()
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"translation_code": "LANGUAGE_NOT_FOUND", "message": f"Language with code '{language_code}' not found"}
        )
    
    # Update fields if provided
    update_data = language_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(language, field, value)
    
    db.commit()
    db.refresh(language)
    
    return language

@router.post("/{language_code}/deactivate", response_model=APIResponse)
async def deactivate_language(
    language_code: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Dezaktywuj język (admin only)"""
    
    language = db.query(Language).filter(Language.code == language_code).first()
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"translation_code": "LANGUAGE_NOT_FOUND", "message": f"Language with code '{language_code}' not found"}
        )
    
    if not language.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "LANGUAGE_ALREADY_INACTIVE", "message": f"Language '{language.name}' is already deactivated"}
        )
    
    language.is_active = False
    db.commit()
    
    return APIResponse(
        success=True,
        type="success",
        translation_code="LANGUAGE_DEACTIVATED",
        message=f"Language '{language.name}' has been deactivated"
    )

@router.delete("/{language_code}", response_model=APIResponse)
async def delete_language(
    language_code: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Usuń język całkowicie (admin only) - tylko jeśli nie ma postów"""
    
    language = db.query(Language).filter(Language.code == language_code).first()
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"translation_code": "LANGUAGE_NOT_FOUND", "message": f"Language with code '{language_code}' not found"}
        )
    
    # Check if language is used by any posts
    from ..models import BlogPostTranslation
    posts_count = db.query(BlogPostTranslation).filter(BlogPostTranslation.language_code == language_code).count()
    
    if posts_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"translation_code": "LANGUAGE_IN_USE", "message": f"Cannot delete language '{language.name}' - it is used by {posts_count} posts. Use deactivate endpoint instead."}
        )
    
    # Safe to delete
    db.delete(language)
    db.commit()
    
    return APIResponse(
        success=True,
        type="success",
        translation_code="LANGUAGE_DELETED",
        message=f"Language '{language.name}' has been permanently deleted"
    )

@router.post("/{language_code}/activate", response_model=APIResponse)
async def activate_language(
    language_code: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Aktywuj dezaktywowany język (admin only)"""
    
    language = db.query(Language).filter(Language.code == language_code).first()
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"translation_code": "LANGUAGE_NOT_FOUND", "message": f"Language with code '{language_code}' not found"}
        )
    
    language.is_active = True
    db.commit()
    
    return APIResponse(
        success=True,
        type="success",
        translation_code="LANGUAGE_ACTIVATED",
        message=f"Language '{language.name}' has been activated"
    )

@router.get("/stats/usage")
async def get_language_usage_stats(
    db: Session = Depends(get_db)
):
    """Pobierz statystyki użycia języków"""
    from ..models import BlogPostTranslation
    from sqlalchemy import func
    
    # Get language usage statistics
    stats = db.query(
        Language.code,
        Language.name,
        Language.native_name,
        Language.is_active,
        func.count(BlogPostTranslation.id).label('posts_count')
    ).outerjoin(
        BlogPostTranslation, Language.code == BlogPostTranslation.language_code
    ).group_by(
        Language.id, Language.code, Language.name, Language.native_name, Language.is_active
    ).order_by(
        func.count(BlogPostTranslation.id).desc()
    ).all()
    
    return {
        "languages": [
            {
                "code": stat.code,
                "name": stat.name,
                "native_name": stat.native_name,
                "is_active": stat.is_active,
                "posts_count": stat.posts_count
            }
            for stat in stats
        ]
    }
