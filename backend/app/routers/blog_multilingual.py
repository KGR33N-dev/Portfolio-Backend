from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timezone
import re

from ..database import get_db
from ..models import BlogPost, BlogPostTranslation, BlogTag, User, Language
from ..schemas import (
    BlogPostCreate, BlogPostUpdate, BlogPostPublic, BlogPostAdmin, 
    BlogPostSingleLanguage, BlogPostTranslationCreate, BlogPostTranslationUpdate,
    APIResponse, PaginatedResponse
)
from ..security import get_current_admin_user

router = APIRouter()

async def validate_language_code(language_code: str, db: Session) -> bool:
    """Sprawdź czy kod języka jest prawidłowy i aktywny"""
    if not language_code:
        return True  # Allow empty language
    
    language = db.query(Language).filter(
        Language.code == language_code,
        Language.is_active == True
    ).first()
    
    return language is not None

def create_slug(title: str) -> str:
    """Create URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)  # Remove special characters
    slug = re.sub(r'[\s-]+', '-', slug)       # Replace spaces/hyphens with single hyphen
    return slug.strip('-')

@router.get("/", response_model=PaginatedResponse)
async def get_blog_posts(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    language: Optional[str] = Query(None, description="Language code (e.g., 'en', 'pl', 'de')"),
    category: Optional[str] = Query(None),
    published_only: bool = Query(True),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    ids: Optional[str] = Query(None, description="Comma-separated list of post IDs"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of results"),
    sort: str = Query("published_at", pattern="^(published_at|created_at|title)$"),
    order: str = Query("desc", pattern="^(asc|desc)$")
):
    """Pobierz wszystkie posty bloga z paginacją i filtrowaniem (wielojęzyczne)"""
    
    # Base query - join with translations
    query = db.query(BlogPost).options(
        joinedload(BlogPost.translations),
        joinedload(BlogPost.tags)
    )
    
    # Filter by publication status
    if published_only:
        query = query.filter(BlogPost.is_published == True)
    
    # Filter by specific IDs if provided
    if ids:
        try:
            id_list = [int(id.strip()) for id in ids.split(',') if id.strip().isdigit()]
            if id_list:
                query = query.filter(BlogPost.id.in_(id_list))
        except ValueError:
            pass
    
    # Filter by category
    if category:
        query = query.filter(BlogPost.category == category)
    
    # Filter by tags
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        if tag_list:
            query = query.join(BlogTag).filter(BlogTag.tag_name.in_(tag_list))
    
    # Order by specified field
    if sort == "published_at":
        if order == "desc":
            query = query.order_by(BlogPost.published_at.desc().nullslast())
        else:
            query = query.order_by(BlogPost.published_at.asc().nullsfirst())
    elif sort == "created_at":
        if order == "desc":
            query = query.order_by(BlogPost.created_at.desc())
        else:
            query = query.order_by(BlogPost.created_at.asc())
    
    # Apply limit if specified (overrides pagination)
    if limit:
        posts = query.limit(limit).all()
        total = len(posts)
    else:
        # Calculate pagination
        total = query.count()
        posts = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Convert to single language view if language specified
    if language:
        posts_data = []
        for post in posts:
            # Find translation for requested language
            translation = next(
                (t for t in post.translations if t.language_code == language), 
                None
            )
            if translation:
                post_dict = {
                    "id": post.id,
                    "slug": post.slug,
                    "title": translation.title,
                    "content": translation.content,
                    "excerpt": translation.excerpt,
                    "author": post.author,
                    "author_id": post.author_id,
                    "meta_title": translation.meta_title,
                    "meta_description": translation.meta_description,
                    "language_code": translation.language_code,
                    "category": post.category,
                    "featured_image": post.featured_image,
                    "created_at": post.created_at,
                    "updated_at": post.updated_at,
                    "is_published": post.is_published,
                    "published_at": post.published_at,
                    "tags": [tag.tag_name for tag in post.tags] if post.tags else []
                }
                posts_data.append(post_dict)
    else:
        # Return full multilingual posts
        posts_data = []
        for post in posts:
            post_dict = {
                "id": post.id,
                "slug": post.slug,
                "author": post.author,
                "author_id": post.author_id,
                "category": post.category,
                "featured_image": post.featured_image,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "is_published": post.is_published,
                "published_at": post.published_at,
                "tags": [tag.tag_name for tag in post.tags] if post.tags else [],
                "translations": [
                    {
                        "id": t.id,
                        "language_code": t.language_code,
                        "title": t.title,
                        "content": t.content,
                        "excerpt": t.excerpt,
                        "meta_title": t.meta_title,
                        "meta_description": t.meta_description,
                        "created_at": t.created_at,
                        "updated_at": t.updated_at
                    } for t in post.translations
                ]
            }
            posts_data.append(post_dict)
    
    return PaginatedResponse(
        items=posts_data,
        total=total,
        page=page if not limit else 1,
        pages=(total + per_page - 1) // per_page if not limit else 1,
        per_page=per_page if not limit else total
    )

@router.put("/{post_id}", response_model=dict)
async def update_blog_post(
    post_id: int,
    post_update: BlogPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Admin endpoint: Zaktualizuj post bloga (wielojęzyczny)"""
    
    # Find the post
    post = db.query(BlogPost).options(
        joinedload(BlogPost.translations),
        joinedload(BlogPost.tags)
    ).filter(BlogPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "POST_NOT_FOUND", "message": "Post not found"}
        )
    
    # Update main post fields
    update_data = post_update.dict(exclude={'translations', 'tags'}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
    
    # Handle publication status
    if hasattr(post_update, 'is_published') and post_update.is_published is not None:
        if post_update.is_published and not post.is_published:
            # Publishing for the first time
            post.published_at = datetime.now(timezone.utc)
        elif not post_update.is_published:
            # Unpublishing
            post.published_at = None
    
    # Update translations
    if hasattr(post_update, 'translations') and post_update.translations:
        for translation_data in post_update.translations:
            # Validate language code
            if not await validate_language_code(translation_data.language_code, db):
                raise HTTPException(
                    status_code=400,
                    detail={"translation_code": "INVALID_LANGUAGE_CODE", "message": f"Invalid language code: {translation_data.language_code}"}
                )
            
            # Find existing translation
            existing_translation = db.query(BlogPostTranslation).filter(
                BlogPostTranslation.post_id == post_id,
                BlogPostTranslation.language_code == translation_data.language_code
            ).first()
            
            if existing_translation:
                # Update existing translation
                translation_update_data = translation_data.dict(exclude_unset=True, exclude={'language_code'})
                for field, value in translation_update_data.items():
                    setattr(existing_translation, field, value)
                existing_translation.updated_at = datetime.now(timezone.utc)
            else:
                # Create new translation
                new_translation = BlogPostTranslation(
                    post_id=post_id,
                    language_code=translation_data.language_code,
                    title=translation_data.title,
                    content=translation_data.content,
                    excerpt=translation_data.excerpt or "",
                    meta_title=translation_data.meta_title or "",
                    meta_description=translation_data.meta_description or ""
                )
                db.add(new_translation)
    
    # Update tags
    if hasattr(post_update, 'tags') and post_update.tags is not None:
        # Delete existing tags
        db.query(BlogTag).filter(BlogTag.post_id == post_id).delete()
        
        # Add new tags
        for tag_name in post_update.tags:
            if tag_name.strip():
                tag = BlogTag(post_id=post_id, tag_name=tag_name.strip())
                db.add(tag)
    
    post.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(post)
    
    # Return updated post with translations
    return {
        "id": post.id,
        "slug": post.slug,
        "author": post.author,
        "author_id": post.author_id,
        "category": post.category,
        "featured_image": post.featured_image,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "is_published": post.is_published,
        "published_at": post.published_at,
        "tags": [tag.tag_name for tag in post.tags] if post.tags else [],
        "translations": [
            {
                "id": t.id,
                "language_code": t.language_code,
                "title": t.title,
                "content": t.content,
                "excerpt": t.excerpt,
                "meta_title": t.meta_title,
                "meta_description": t.meta_description,
                "created_at": t.created_at,
                "updated_at": t.updated_at
            } for t in post.translations
        ]
    }

@router.get("/{slug}", response_model=dict)
async def get_blog_post_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    language: Optional[str] = Query(None, description="Language code")
):
    """Pobierz pojedynczy post po slug"""
    post = db.query(BlogPost).options(
        joinedload(BlogPost.translations),
        joinedload(BlogPost.tags)
    ).filter(BlogPost.slug == slug).first()
    
    if not post:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "POST_NOT_FOUND", "message": "Post not found"}
        )
    
    if language:
        # Return single language version
        translation = next(
            (t for t in post.translations if t.language_code == language), 
            None
        )
        if not translation:
            raise HTTPException(
                status_code=404, 
                detail={"translation_code": "TRANSLATION_NOT_FOUND", "message": f"Translation for language '{language}' not found"}
            )
        
        return {
            "id": post.id,
            "slug": post.slug,
            "title": translation.title,
            "content": translation.content,
            "excerpt": translation.excerpt,
            "author": post.author,
            "author_id": post.author_id,
            "meta_title": translation.meta_title,
            "meta_description": translation.meta_description,
            "language_code": translation.language_code,
            "category": post.category,
            "featured_image": post.featured_image,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "is_published": post.is_published,
            "published_at": post.published_at,
            "tags": [tag.tag_name for tag in post.tags] if post.tags else []
        }
    else:
        # Return full multilingual post
        return {
            "id": post.id,
            "slug": post.slug,
            "author": post.author,
            "author_id": post.author_id,
            "category": post.category,
            "featured_image": post.featured_image,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "is_published": post.is_published,
            "published_at": post.published_at,
            "tags": [tag.tag_name for tag in post.tags] if post.tags else [],
            "translations": [
                {
                    "id": t.id,
                    "language_code": t.language_code,
                    "title": t.title,
                    "content": t.content,
                    "excerpt": t.excerpt,
                    "meta_title": t.meta_title,
                    "meta_description": t.meta_description,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at
                } for t in post.translations
            ]
        }

@router.post("/", response_model=BlogPostPublic)
async def create_blog_post(
    post: BlogPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Utwórz nowy post bloga (wielojęzyczny)"""
    
    # Check if slug is unique
    existing_post = db.query(BlogPost).filter(BlogPost.slug == post.slug).first()
    if existing_post:
        raise HTTPException(
            status_code=400,
            detail={"translation_code": "SLUG_EXISTS", "message": "Slug already exists"}
        )
    
    # Validate all language codes
    for translation in post.translations:
        if not await validate_language_code(translation.language_code, db):
            raise HTTPException(
                status_code=400,
                detail={"translation_code": "INVALID_LANGUAGE_CODE", "message": f"Invalid language code: {translation.language_code}"}
            )
    
    # Create main blog post
    db_post = BlogPost(
        slug=post.slug,
        author=post.author,
        author_id=current_user.id,
        category=post.category,
        featured_image=post.featured_image
    )
    db.add(db_post)
    db.flush()  # Get the ID
    
    # Create translations
    for translation_data in post.translations:
        translation = BlogPostTranslation(
            post_id=db_post.id,
            language_code=translation_data.language_code,
            title=translation_data.title,
            content=translation_data.content,
            excerpt=translation_data.excerpt,
            meta_title=translation_data.meta_title,
            meta_description=translation_data.meta_description
        )
        db.add(translation)
    
    # Add tags
    if post.tags:
        for tag_name in post.tags:
            tag = BlogTag(post_id=db_post.id, tag_name=tag_name.strip())
            db.add(tag)
    
    db.commit()
    db.refresh(db_post)
    
    return db_post

# Admin endpoints
@router.get("/admin/posts", response_model=PaginatedResponse)
async def get_admin_blog_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: str = Query("all", pattern="^(all|published|draft)$"),
    category: Optional[str] = Query(None),
    published_only: Optional[bool] = Query(None, description="Legacy parameter")
):
    """Admin endpoint: Pobierz wszystkie posty (w tym nieopublikowane)"""
    
    query = db.query(BlogPost).options(
        joinedload(BlogPost.translations),
        joinedload(BlogPost.tags)
    )
    
    # Filter by category
    if category:
        query = query.filter(BlogPost.category == category)
    
    # Handle status filter
    if status == "published":
        query = query.filter(BlogPost.is_published == True)
    elif status == "draft":
        query = query.filter(BlogPost.is_published == False)
    elif published_only is not None:
        # Legacy parameter support
        query = query.filter(BlogPost.is_published == published_only)
    # If status="all" or no filter, show all posts
    
    # Order by creation date (newest first), then by published date
    query = query.order_by(BlogPost.created_at.desc(), BlogPost.published_at.desc())
    
    # Calculate pagination
    total = query.count()
    posts = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Convert posts to response format with admin details
    posts_data = []
    for post in posts:
        post_dict = {
            "id": post.id,
            "slug": post.slug,
            "author": post.author,
            "author_id": post.author_id,
            "category": post.category,
            "featured_image": post.featured_image,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "is_published": post.is_published,
            "published_at": post.published_at,
            "tags": [tag.tag_name for tag in post.tags] if post.tags else [],
            "translations": [
                {
                    "id": t.id,
                    "language_code": t.language_code,
                    "title": t.title,
                    "content": t.content,
                    "excerpt": t.excerpt,
                    "meta_title": t.meta_title,
                    "meta_description": t.meta_description,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at
                } for t in post.translations
            ]
        }
        posts_data.append(post_dict)
    
    return PaginatedResponse(
        items=posts_data,
        total=total,
        page=page,
        pages=(total + per_page - 1) // per_page,
        per_page=per_page
    )

@router.put("/{post_id}/publish", response_model=APIResponse)
async def publish_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Admin endpoint: Opublikuj post"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "POST_NOT_FOUND", "message": "Post not found"}
        )
    
    post.is_published = True
    post.published_at = datetime.now(timezone.utc)
    db.commit()

    return APIResponse(success=True,type="success",translation_code="POST_PUBLISHED", message="Post published successfully")

@router.put("/{post_id}/unpublish", response_model=APIResponse)
async def unpublish_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Admin endpoint: Cofnij publikację posta"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "POST_NOT_FOUND", "message": "Post not found"}
        )
    
    post.is_published = False
    post.published_at = None
    db.commit()

    return APIResponse(success=True, type="success", translation_code="POST_UNPUBLISHED", message="Post unpublished successfully")

# Translation management endpoints
@router.post("/{post_id}/translations", response_model=dict)
async def add_translation(
    post_id: int,
    translation: BlogPostTranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Dodaj tłumaczenie do istniejącego posta"""
    
    # Check if post exists
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "POST_NOT_FOUND", "message": "Post not found"}
        )
    
    # Validate language code
    if not await validate_language_code(translation.language_code, db):
        raise HTTPException(
            status_code=400,
            detail={"translation_code": "INVALID_LANGUAGE_CODE", "message": f"Invalid language code: {translation.language_code}"}
        )
    
    # Check if translation already exists
    existing = db.query(BlogPostTranslation).filter(
        BlogPostTranslation.post_id == post_id,
        BlogPostTranslation.language_code == translation.language_code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail={"translation_code": "TRANSLATION_EXISTS", "message": f"Translation for language '{translation.language_code}' already exists"}
        )
    
    # Create translation
    db_translation = BlogPostTranslation(
        post_id=post_id,
        language_code=translation.language_code,
        title=translation.title,
        content=translation.content,
        excerpt=translation.excerpt,
        meta_title=translation.meta_title,
        meta_description=translation.meta_description
    )
    
    db.add(db_translation)
    db.commit()
    db.refresh(db_translation)
    
    return {
        "id": db_translation.id,
        "language_code": db_translation.language_code,
        "title": db_translation.title,
        "content": db_translation.content,
        "excerpt": db_translation.excerpt,
        "meta_title": db_translation.meta_title,
        "meta_description": db_translation.meta_description,
        "created_at": db_translation.created_at,
        "updated_at": db_translation.updated_at
    }

@router.put("/{post_id}/translations/{language_code}", response_model=dict)
async def update_translation(
    post_id: int,
    language_code: str,
    translation_update: BlogPostTranslationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Zaktualizuj tłumaczenie posta"""
    
    translation = db.query(BlogPostTranslation).filter(
        BlogPostTranslation.post_id == post_id,
        BlogPostTranslation.language_code == language_code
    ).first()
    
    if not translation:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "TRANSLATION_NOT_FOUND", "message": f"Translation for language '{language_code}' not found"}
        )
    
    # Update fields
    update_data = translation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(translation, field, value)
    
    translation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(translation)
    
    return {
        "id": translation.id,
        "language_code": translation.language_code,
        "title": translation.title,
        "content": translation.content,
        "excerpt": translation.excerpt,
        "meta_title": translation.meta_title,
        "meta_description": translation.meta_description,
        "created_at": translation.created_at,
        "updated_at": translation.updated_at
    }

@router.delete("/{post_id}/translations/{language_code}", response_model=APIResponse)
async def delete_translation(
    post_id: int,
    language_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Usuń tłumaczenie posta"""
    
    translation = db.query(BlogPostTranslation).filter(
        BlogPostTranslation.post_id == post_id,
        BlogPostTranslation.language_code == language_code
    ).first()
    
    if not translation:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "TRANSLATION_NOT_FOUND", "message": f"Translation for language '{language_code}' not found"}
        )
    
    # Check if this is the last translation
    translation_count = db.query(BlogPostTranslation).filter(
        BlogPostTranslation.post_id == post_id
    ).count()
    
    if translation_count <= 1:
        raise HTTPException(
            status_code=400,
            detail={"translation_code": "LAST_TRANSLATION", "message": "Cannot delete the last translation. A post must have at least one translation."}
        )
    
    db.delete(translation)
    db.commit()

    return APIResponse(success=True, type="success", translation_code="TRANSLATION_DELETED", message="Translation deleted successfully")

@router.delete("/{post_id}", response_model=APIResponse)
async def delete_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Admin endpoint: Usuń post (wraz z wszystkimi tłumaczeniami)"""
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "POST_NOT_FOUND", "message": "Post not found"}
        )
    
    # Delete related tags
    db.query(BlogTag).filter(BlogTag.post_id == post_id).delete()
    
    # Delete translations (cascade should handle this, but being explicit)
    db.query(BlogPostTranslation).filter(BlogPostTranslation.post_id == post_id).delete()
    
    # Delete post
    db.delete(post)
    db.commit()

    return APIResponse(success=True, type="success", translation_code="POST_DELETED", message="Post deleted successfully")
