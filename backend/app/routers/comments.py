"""
Comments router for blog posts
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from ..database import get_db
from ..models import Comment, CommentLike, BlogPost, User, UserRoleEnum
from ..schemas import CommentCreate, CommentUpdate, CommentLikeCreate, Comment as CommentSchema, CommentWithReplies, APIResponse, PaginatedResponse
from ..security import get_current_user, get_current_user_optional
from ..rank_utils import update_user_stats

router = APIRouter()

def make_timezone_aware(dt):
    """Convert naive datetime to UTC timezone-aware datetime"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.client.host

def build_comment_response(comment: Comment, current_user: Optional[User] = None, include_replies: bool = False) -> dict:
    """Build comment response with like counts and user like status"""
    
    # Count likes and dislikes
    likes_count = len([like for like in comment.likes if like.is_like])
    dislikes_count = len([like for like in comment.likes if not like.is_like])
    
    # Get user's like status
    user_like_status = None
    if current_user:
        user_like = next((like for like in comment.likes if like.user_id == current_user.id), None)
        if user_like:
            user_like_status = user_like.is_like
    
    # Count replies
    replies_count = len([reply for reply in comment.replies if not reply.is_deleted])
    
    # Check permissions for current user
    can_edit = False
    can_delete = False
    
    if current_user and not comment.is_deleted:
        # can_edit: tylko właściciel + czas < 15 min
        if comment.user_id == current_user.id:
            # Ensure both datetimes are timezone-aware for comparison
            current_time = datetime.now(timezone.utc)
            created_at = make_timezone_aware(comment.created_at)
            time_since_creation = current_time - created_at
            if time_since_creation <= timedelta(minutes=15):
                can_edit = True
        
        # can_delete: właściciel/moderator/admin
        if comment.user_id == current_user.id:
            can_delete = True
        elif current_user.role and current_user.role.name == UserRoleEnum.ADMIN:
            can_delete = True
        elif current_user.role and current_user.role.name == UserRoleEnum.MODERATOR:
            can_delete = True
    
    # Build author info with role and rank
    author_info = {
        "id": comment.user.id if comment.user else None,
        "username": comment.user.username if comment.user else "Usunięty użytkownik",
        "role": {
            "id": comment.user.role.id if comment.user and comment.user.role else None,
            "name": comment.user.role.name if comment.user and comment.user.role else None,
            "display_name": comment.user.role.display_name if comment.user and comment.user.role else None,
            "color": comment.user.role.color if comment.user and comment.user.role else None,
            "level": comment.user.role.level if comment.user and comment.user.role else 0,
        } if comment.user and comment.user.role else None,
        "rank": {
            "id": comment.user.rank.id if comment.user and comment.user.rank else None,
            "name": comment.user.rank.name if comment.user and comment.user.rank else None,
            "display_name": comment.user.rank.display_name if comment.user and comment.user.rank else None,
            "color": comment.user.rank.color if comment.user and comment.user.rank else None,
            "level": comment.user.rank.level if comment.user and comment.user.rank else 0,
            "icon": comment.user.rank.icon if comment.user and comment.user.rank else None
        } if comment.user and comment.user.rank else None
    }
    
    comment_data = {
        "id": comment.id,
        "post_id": comment.post_id,
        "user_id": comment.user_id,
        "parent_id": comment.parent_id,
        "content": comment.content if not comment.is_deleted else "[Komentarz został usunięty]",
        "is_deleted": comment.is_deleted,
        "author": author_info,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
        "likes_count": likes_count,
        "dislikes_count": dislikes_count,
        "user_like_status": user_like_status,
        "replies_count": replies_count,
        "can_edit": can_edit,
        "can_delete": can_delete
    }
    
    if include_replies:
        comment_data["replies"] = [
            build_comment_response(reply, current_user, False) 
            for reply in comment.replies 
        ]
    
    return comment_data

@router.get("/post/{post_id}", response_model=List[dict])
async def get_post_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at", pattern="^(created_at|likes)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    include_replies: bool = Query(True, description="Include replies in response")
):
    """Pobierz komentarze dla posta"""
    
    # Check if post exists
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "POST_NOT_FOUND", "message": "Post not found"}
        )
    
    # Base query - only top-level comments (no parent)
    # Eager load user with role and rank to avoid N+1 queries
    query = db.query(Comment).options(
        joinedload(Comment.user).joinedload(User.role),
        joinedload(Comment.user).joinedload(User.rank),
        joinedload(Comment.likes),
        joinedload(Comment.replies).joinedload(Comment.user).joinedload(User.role),
        joinedload(Comment.replies).joinedload(Comment.user).joinedload(User.rank)
    ).filter(
        Comment.post_id == post_id,
        Comment.parent_id.is_(None)
    )
    
    # Sorting
    if sort == "created_at":
        if order == "desc":
            query = query.order_by(Comment.created_at.desc())
        else:
            query = query.order_by(Comment.created_at.asc())
    elif sort == "likes":
        # Sort by like count (likes - dislikes)
        if order == "desc":
            query = query.outerjoin(CommentLike).group_by(Comment.id).order_by(
                func.sum(func.case([(CommentLike.is_like == True, 1)], else_=0)).desc(),
                Comment.created_at.desc()
            )
        else:
            query = query.outerjoin(CommentLike).group_by(Comment.id).order_by(
                func.sum(func.case([(CommentLike.is_like == True, 1)], else_=0)).asc(),
                Comment.created_at.asc()
            )
    
    # Pagination
    total = query.count()
    comments = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Build response
    comments_data = [
        build_comment_response(comment, current_user, include_replies)
        for comment in comments
    ]
    
    return comments_data

@router.post("/post/{post_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Wymagane - tylko zalogowani użytkownicy
):
    """Dodaj komentarz do posta (tylko zalogowani użytkownicy)"""
    
    # Check if post exists and is published
    post = db.query(BlogPost).filter(
        BlogPost.id == post_id,
        BlogPost.is_published == True
    ).first()
    if not post:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "POST_NOT_FOUND", "message": "Post not found or not published"}
        )
    
    # Check if parent comment exists (for replies)
    if comment_data.parent_id:
        parent_comment = db.query(Comment).filter(
            Comment.id == comment_data.parent_id,
            Comment.post_id == post_id
        ).first()
        if not parent_comment:
            raise HTTPException(
                status_code=404, 
                detail={"translation_code": "PARENT_COMMENT_NOT_FOUND", "message": "Parent comment not found"}
            )
        
        # 🎯 OGRANICZENIE GŁĘBOKOŚCI: Maksymalnie 2 poziomy komentarzy
        if parent_comment.parent_id is not None:
            raise HTTPException(
                status_code=400,
                detail={"translation_code": "MAX_COMMENT_DEPTH", "message": "Nie można odpowiadać na odpowiedzi. Maksymalnie 2 poziomy komentarzy."}
            )    # Create comment (tylko dla zalogowanych użytkowników)
    new_comment = Comment(
        post_id=post_id,
        user_id=current_user.id,  # Wymagane - użytkownik musi być zalogowany
        parent_id=comment_data.parent_id,
        content=comment_data.content,
        ip_address=get_client_ip(request)
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    # 🎉 AUTOMATYCZNE SPRAWDZENIE AWANSU RANGI
    # Aktualizuj statystyki użytkownika i sprawdź awans
    rank_update = update_user_stats(current_user.id, db, "comment")
    
    # Load relationships for response
    # Load comment with all relationships for response
    new_comment = db.query(Comment).options(
        joinedload(Comment.user).joinedload(User.role),
        joinedload(Comment.user).joinedload(User.rank),
        joinedload(Comment.likes),
        joinedload(Comment.replies)
    ).filter(Comment.id == new_comment.id).first()
    
    # Dodaj info o awansie do odpowiedzi
    response = build_comment_response(new_comment, current_user)
    if rank_update.get("rank_check", {}).get("upgraded"):
        response["rank_upgrade"] = rank_update["rank_check"]
    
    return response

@router.put("/{comment_id}", response_model=dict)
async def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edytuj komentarz - tylko właściciel może edytować swój komentarz (do 15 minut od utworzenia)"""
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "COMMENT_NOT_FOUND", "message": "Comment not found"}
        )
    
    # 🔐 SPRAWDZANIE UPRAWNIEŃ DO EDYCJI
    # Tylko właściciel komentarza może go edytować (moderatorzy i admini NIE mogą edytować cudzych komentarzy)
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail={"translation_code": "COMMENT_EDIT_PERMISSION", "message": "Możesz edytować tylko swoje komentarze"}
        )
    
    # Check if comment is not too old (e.g., 15 minutes edit window)
    current_time = datetime.now(timezone.utc)
    created_at = make_timezone_aware(comment.created_at)
    if current_time - created_at > timedelta(minutes=15):
        raise HTTPException(
            status_code=403, 
            detail={"translation_code": "COMMENT_EDIT_TIMEOUT", "message": "Czas na edycję komentarza minął (15 minut)"}
        )
    
    comment.content = comment_data.content
    comment.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(comment)
    
    # Load relationships for response
    comment = db.query(Comment).options(
        joinedload(Comment.user).joinedload(User.role),
        joinedload(Comment.user).joinedload(User.rank),
        joinedload(Comment.likes),
        joinedload(Comment.replies)
    ).filter(Comment.id == comment.id).first()
    
    return build_comment_response(comment, current_user)

@router.delete("/{comment_id}", response_model=APIResponse)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Usuń komentarz - właściciel, moderator lub admin (soft delete)"""
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "COMMENT_NOT_FOUND", "message": "Comment not found"}
        )
    
    # 🔐 SPRAWDZANIE UPRAWNIEŃ DO USUWANIA
    can_delete = False
    delete_reason = ""
    
    # 1. Właściciel komentarza może go usunąć
    if comment.user_id == current_user.id:
        can_delete = True
        delete_reason = "własny komentarz"
    
    # 2. Administrator może usunąć każdy komentarz
    elif current_user.role and current_user.role.name == UserRoleEnum.ADMIN:
        can_delete = True
        delete_reason = "uprawnienia administratora"
    
    # 3. Moderator może usunąć każdy komentarz
    elif current_user.role and current_user.role.name == UserRoleEnum.MODERATOR:
        can_delete = True
        delete_reason = "uprawnienia moderatora"
    
    if not can_delete:
        raise HTTPException(
            status_code=403, 
            detail={"translation_code": "COMMENT_DELETE_PERMISSION", "message": "Nie masz uprawnień do usunięcia tego komentarza. Możesz usuwać tylko swoje komentarze."}
        )
    
    # Soft delete
    comment.is_deleted = True
    
    db.commit()
    
    return APIResponse(
        success=True,
        type="success",
        translation_code="COMMENT_DELETED",
        message=f"Komentarz został usunięty ({delete_reason})"
    )

@router.post("/{comment_id}/like", response_model=APIResponse)
async def like_comment(
    comment_id: int,
    like_data: CommentLikeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Polub lub nie lubię komentarza"""
    
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.is_deleted == False
    ).first()
    if not comment:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "COMMENT_NOT_FOUND", "message": "Comment not found"}
        )
    
    # 🚫 WALIDACJA: Użytkownik nie może polubić własnych komentarzy
    if comment.user_id == current_user.id:
        raise HTTPException(
            status_code=400, 
            detail={"translation_code": "SELF_LIKE_ERROR", "message": "Nie możesz polubić własnego komentarza"}
        )
    
    # Check if user already liked/disliked this comment
    existing_like = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id,
        CommentLike.user_id == current_user.id
    ).first()
    
    if existing_like:
        if existing_like.is_like == like_data.is_like:
            # Same action - remove like/dislike
            db.delete(existing_like)
            action = "removed"
        else:
            # Different action - update like/dislike
            existing_like.is_like = like_data.is_like
            action = "updated"
    else:
        # New like/dislike
        new_like = CommentLike(
            comment_id=comment_id,
            user_id=current_user.id,
            is_like=like_data.is_like
        )
        db.add(new_like)
        action = "added"
    
    db.commit()
    
    # 🎉 AUTOMATYCZNE SPRAWDZENIE AWANSU RANGI
    # Sprawdź awans dla właściciela komentarza jeśli otrzymał lajka
    rank_update_info = None
    if like_data.is_like and action in ["added", "updated"]:
        # Właściciel komentarza otrzymał lajka
        rank_update = update_user_stats(comment.user_id, db, "like_received")
        if rank_update.get("rank_check", {}).get("upgraded"):
            rank_update_info = rank_update["rank_check"]
    
    like_type = "like" if like_data.is_like else "dislike"
    response_data = {
        "success": True,
        "type": "success",
        "translation_code": "COMMENT_LIKE_SUCCESS",
        "message": f"Comment {like_type} {action} successfully"
    }
    
    # Dodaj info o awansie właściciela komentarza
    if rank_update_info:
        response_data["comment_author_rank_upgrade"] = rank_update_info
    
    return APIResponse(**response_data)

@router.get("/{comment_id}/replies", response_model=List[dict])
async def get_comment_replies(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Pobierz odpowiedzi na komentarz"""
    
    # Check if parent comment exists
    parent_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not parent_comment:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "COMMENT_NOT_FOUND", "message": "Comment not found"}
        )
    
    # Get replies with eager loading of user roles and ranks
    query = db.query(Comment).options(
        joinedload(Comment.user).joinedload(User.role),
        joinedload(Comment.user).joinedload(User.rank),
        joinedload(Comment.likes),
        joinedload(Comment.replies)
    ).filter(
        Comment.parent_id == comment_id
    ).order_by(Comment.created_at.asc())
    
    # Pagination
    total = query.count()
    replies = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Build response
    replies_data = [
        build_comment_response(reply, current_user, False)
        for reply in replies
    ]
    
    return replies_data

@router.get("/stats/{post_id}")
async def get_post_comment_stats(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Pobierz statystyki komentarzy dla posta"""
    
    # Check if post exists
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=404, 
            detail={"translation_code": "POST_NOT_FOUND", "message": "Post not found"}
        )
    
    # Get stats
    total_comments = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.is_deleted == False
    ).count()
    
    total_replies = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.parent_id.isnot(None),
        Comment.is_deleted == False
    ).count()
    
    return {
        "post_id": post_id,
        "total_comments": total_comments,
        "total_replies": total_replies,
        "total_interactions": total_comments
    }
