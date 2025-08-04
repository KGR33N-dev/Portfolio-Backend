from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import re

from ..database import get_db
from ..models import BlogPost, BlogTag, User, Language
from ..schemas import BlogPostCreate, BlogPostUpdate, BlogPostPublic, BlogPostAdmin, APIResponse, PaginatedResponse
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
    """Pobierz wszystkie posty bloga z paginacją i filtrowaniem"""
    query = db.query(BlogPost)
    
    # Filter by specific IDs if provided
    if ids:
        try:
            id_list = [int(id.strip()) for id in ids.split(',') if id.strip()]
            query = query.filter(BlogPost.id.in_(id_list))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ID format in 'ids' parameter")
    
    # Filter by language if specified
    if language:
        # Validate language code
        if not await validate_language_code(language, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Language code '{language}' is not valid or active"
            )
        query = query.filter(BlogPost.language == language)
    
    # Filter by category if specified
    if category:
        query = query.filter(BlogPost.category == category)
    
    # Filter by tags if specified
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        for tag in tag_list:
            query = query.filter(BlogPost.tags.any(BlogTag.tag_name == tag))
    
    # Filter published posts for public API
    if published_only:
        query = query.filter(BlogPost.is_published == True)
    
    # Apply sorting
    if sort == "published_at":
        if order == "desc":
            query = query.order_by(BlogPost.published_at.desc().nullslast(), BlogPost.created_at.desc())
        else:
            query = query.order_by(BlogPost.published_at.asc().nullsfirst(), BlogPost.created_at.asc())
    elif sort == "created_at":
        if order == "desc":
            query = query.order_by(BlogPost.created_at.desc())
        else:
            query = query.order_by(BlogPost.created_at.asc())
    elif sort == "title":
        if order == "desc":
            query = query.order_by(BlogPost.title.desc())
        else:
            query = query.order_by(BlogPost.title.asc())
    
    # Apply limit if specified (overrides pagination)
    if limit:
        posts = query.limit(limit).all()
        total = len(posts)
        pages = 1
        current_page = 1
        items_per_page = limit
    else:
        # Calculate pagination
        total = query.count()
        posts = query.offset((page - 1) * per_page).limit(per_page).all()
        pages = (total + per_page - 1) // per_page
        current_page = page
        items_per_page = per_page
    
    # Convert posts to response format
    posts_data = []
    for post in posts:
        post_dict = {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "content": post.content,
            "excerpt": post.excerpt,
            "author": post.author,
            "meta_title": post.meta_title,
            "meta_description": post.meta_description,
            "language": post.language,
            "category": post.category,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "is_published": post.is_published,
            "published_at": post.published_at,
            "featured_image": post.featured_image,
            "tags": [tag.tag_name for tag in post.tags] if post.tags else []
        }
        posts_data.append(post_dict)
    
    return PaginatedResponse(
        items=posts_data,
        total=total,
        page=current_page,
        pages=pages,
        per_page=items_per_page
    )

@router.get("/slug/{slug}", response_model=BlogPostPublic)
async def get_blog_post_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    language: Optional[str] = Query(None, pattern="^(pl|en)$"),
    include_unpublished: bool = Query(False)
):
    """Pobierz pojedynczy post po slug"""
    query = db.query(BlogPost).filter(BlogPost.slug == slug)
    
    # Filter by language if specified
    if language:
        query = query.filter(BlogPost.language == language)
    
    if not include_unpublished:
        query = query.filter(BlogPost.is_published == True)
    
    post = query.first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post nie został znaleziony"
        )
    
    # Format response with tags
    post_dict = {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "excerpt": post.excerpt,
        "author": post.author,
        "meta_title": post.meta_title,
        "meta_description": post.meta_description,
        "language": post.language,
        "category": post.category,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "is_published": post.is_published,
        "published_at": post.published_at,
        "featured_image": post.featured_image,
        "tags": [tag.tag_name for tag in post.tags] if post.tags else []
    }
    
    return post_dict

@router.get("/{post_id}", response_model=BlogPostPublic)
async def get_blog_post_by_id(
    post_id: int,
    db: Session = Depends(get_db),
    include_unpublished: bool = Query(False)
):
    """Pobierz pojedynczy post po ID"""
    query = db.query(BlogPost).filter(BlogPost.id == post_id)
    
    if not include_unpublished:
        query = query.filter(BlogPost.is_published == True)
    
    post = query.first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post nie został znaleziony"
        )
    
    # Format response with tags
    post_dict = {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "excerpt": post.excerpt,
        "author": post.author,
        "meta_title": post.meta_title,
        "meta_description": post.meta_description,
        "language": post.language,
        "category": post.category,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "is_published": post.is_published,
        "published_at": post.published_at,
        "tags": [tag.tag_name for tag in post.tags] if post.tags else []
    }
    
    return post_dict

@router.post("/", response_model=BlogPostPublic, status_code=status.HTTP_201_CREATED)
async def create_blog_post(
    post_data: BlogPostCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create new blog post (admin only)"""
    
    # Validate language code
    if not await validate_language_code(post_data.language, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language code '{post_data.language}' is not valid or active"
        )
    
    # Check if slug already exists
    existing_post = db.query(BlogPost).filter(BlogPost.slug == post_data.slug).first()
    if existing_post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Post with slug '{post_data.slug}' already exists"
        )
    
    # Create new post
    new_post = BlogPost(
        title=post_data.title,
        slug=post_data.slug,
        content=post_data.content,
        excerpt=post_data.excerpt,
        author=post_data.author,
        author_id=current_user.id,  # Set the authenticated user as author
        meta_title=post_data.meta_title or post_data.title,
        meta_description=post_data.meta_description or post_data.excerpt,
        language=post_data.language,
        category=post_data.category,
        featured_image=post_data.featured_image
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # Add tags if provided
    if post_data.tags:
        for tag_name in post_data.tags:
            tag = BlogTag(post_id=new_post.id, tag_name=tag_name.strip())
            db.add(tag)
        db.commit()
        db.refresh(new_post)
    
    return new_post

@router.put("/{post_id}", response_model=BlogPostPublic)
async def update_blog_post(
    post_id: int,
    post_data: BlogPostUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update existing blog post (admin only)"""
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Update fields if provided
    update_data = post_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field != "tags":  # Handle tags separately
            setattr(post, field, value)
    
    # Handle publishing
    if post_data.is_published is True and not post.is_published:
        post.published_at = datetime.utcnow()
    elif post_data.is_published is False:
        post.published_at = None
    
    db.commit()
    
    # Update tags if provided
    if post_data.tags is not None:
        # Remove existing tags
        db.query(BlogTag).filter(BlogTag.post_id == post.id).delete()
        # Add new tags
        for tag_name in post_data.tags:
            tag = BlogTag(post_id=post.id, tag_name=tag_name.strip())
            db.add(tag)
        db.commit()
    
    db.refresh(post)
    return post

@router.delete("/{post_id}", response_model=APIResponse)
async def delete_blog_post(
    post_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete blog post (admin only)"""
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Delete tags first (foreign key constraint)
    db.query(BlogTag).filter(BlogTag.post_id == post.id).delete()
    
    # Delete post
    db.delete(post)
    db.commit()
    
    return APIResponse(
        success=True,
        message=f"Post '{post.title}' has been deleted"
    )

@router.put("/{post_id}/publish", response_model=BlogPostPublic)
async def publish_blog_post(
    post_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Publish blog post (admin only)"""
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    post.is_published = True
    post.published_at = datetime.utcnow()
    
    db.commit()
    db.refresh(post)
    
    return post

@router.get("/admin/posts", response_model=PaginatedResponse)
async def get_admin_blog_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    language: Optional[str] = Query(None, pattern="^(pl|en)$"),
    category: Optional[str] = Query(None),
    published_only: Optional[bool] = Query(None),
    status: Optional[str] = Query(None, pattern="^(published|draft|all)$")
):
    """Admin endpoint: Pobierz wszystkie posty (w tym nieopublikowane) z paginacją"""
    query = db.query(BlogPost)
    
    # Filter by language if specified
    if language:
        query = query.filter(BlogPost.language == language)
    
    # Filter by category if specified
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
            "title": post.title,
            "slug": post.slug,
            "content": post.content,
            "excerpt": post.excerpt,
            "author": post.author,
            "author_id": post.author_id,  # Include author_id for admin
            "meta_title": post.meta_title,
            "meta_description": post.meta_description,
            "language": post.language,
            "category": post.category,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "is_published": post.is_published,
            "published_at": post.published_at,
            "tags": [tag.tag_name for tag in post.tags] if post.tags else []
        }
        posts_data.append(post_dict)
    
    return PaginatedResponse(
        items=posts_data,
        total=total,
        page=page,
        pages=(total + per_page - 1) // per_page,
        per_page=per_page
    )

@router.get("/admin/posts/{post_id}", response_model=BlogPostAdmin)
async def get_admin_blog_post_by_id(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Admin endpoint: Pobierz pojedynczy post po ID (w tym nieopublikowane)"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post nie został znaleziony"
        )
    
    # Format response with tags and admin details
    post_dict = {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "content": post.content,
        "excerpt": post.excerpt,
        "author": post.author,
        "author_id": post.author_id,  # Include author_id for admin
        "meta_title": post.meta_title,
        "meta_description": post.meta_description,
        "language": post.language,
        "category": post.category,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "is_published": post.is_published,
        "published_at": post.published_at,
        "tags": [tag.tag_name for tag in post.tags] if post.tags else []
    }
    
    return post_dict

@router.get("/categories/list")
async def get_categories(db: Session = Depends(get_db)):
    """Pobierz listę wszystkich kategorii"""
    categories = db.query(BlogPost.category).distinct().all()
    return {"categories": [cat[0] for cat in categories]}

@router.get("/tags/list")
async def get_tags(db: Session = Depends(get_db)):
    """Pobierz listę wszystkich tagów"""
    tags = db.query(BlogTag.tag_name).distinct().all()
    return {"tags": [tag[0] for tag in tags]}
