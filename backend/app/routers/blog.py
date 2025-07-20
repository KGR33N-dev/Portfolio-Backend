from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import re

from ..database import get_db
from ..models import BlogPost, BlogTag
from ..schemas import BlogPostCreate, BlogPostUpdate, BlogPostPublic, BlogPostAdmin, APIResponse, PaginatedResponse

router = APIRouter()

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
    language: Optional[str] = Query(None, regex="^(pl|en)$"),
    category: Optional[str] = Query(None),
    published_only: bool = Query(True)
):
    """Pobierz wszystkie posty bloga z paginacją"""
    query = db.query(BlogPost)
    
    # Filter by language if specified
    if language:
        query = query.filter(BlogPost.language == language)
    
    # Filter by category if specified
    if category:
        query = query.filter(BlogPost.category == category)
    
    # Filter published posts for public API
    if published_only:
        query = query.filter(BlogPost.is_published == True)
    
    # Order by publication date (newest first)
    query = query.order_by(BlogPost.published_at.desc(), BlogPost.created_at.desc())
    
    # Calculate pagination
    total = query.count()
    posts = query.offset((page - 1) * per_page).limit(per_page).all()
    
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

@router.get("/{slug}", response_model=BlogPostPublic)
async def get_blog_post_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    include_unpublished: bool = Query(False)
):
    """Pobierz pojedynczy post po slug"""
    query = db.query(BlogPost).filter(BlogPost.slug == slug)
    
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
    db: Session = Depends(get_db)
):
    """Utwórz nowy post bloga"""
    
    # Check if slug already exists
    existing_post = db.query(BlogPost).filter(BlogPost.slug == post_data.slug).first()
    if existing_post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Post ze slug '{post_data.slug}' już istnieje"
        )
    
    # Create new post
    new_post = BlogPost(
        title=post_data.title,
        slug=post_data.slug,
        content=post_data.content,
        excerpt=post_data.excerpt,
        author=post_data.author,
        meta_title=post_data.meta_title or post_data.title,
        meta_description=post_data.meta_description or post_data.excerpt,
        language=post_data.language,
        category=post_data.category
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
    db: Session = Depends(get_db)
):
    """Aktualizuj istniejący post"""
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post nie został znaleziony"
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
    db: Session = Depends(get_db)
):
    """Usuń post bloga"""
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post nie został znaleziony"
        )
    
    # Delete tags first (foreign key constraint)
    db.query(BlogTag).filter(BlogTag.post_id == post.id).delete()
    
    # Delete post
    db.delete(post)
    db.commit()
    
    return APIResponse(
        success=True,
        message=f"Post '{post.title}' został usunięty"
    )

@router.put("/{post_id}/publish", response_model=BlogPostPublic)
async def publish_blog_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Opublikuj post"""
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post nie został znaleziony"
        )
    
    post.is_published = True
    post.published_at = datetime.utcnow()
    
    db.commit()
    db.refresh(post)
    
    return post

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
