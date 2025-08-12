"""
System ról i rang użytkowników - dokumentacja i inicjalizacja
"""

from sqlalchemy.orm import Session
from app.models import UserRole, UserRank, UserRoleEnum, UserRankEnum

def init_roles_and_ranks(db: Session):
    """Inicjalizacja podstawowych ról i rang w systemie"""
    
    # 🎯 ROLE UŻYTKOWNIKÓW
    roles_data = [
        {
            "name": UserRoleEnum.USER,
            "display_name": "Użytkownik",
            "description": "Zwykły użytkownik bloga",
            "color": "#6c757d",
            "permissions": ["comment.create", "comment.like", "profile.edit"],
            "level": 1
        },
        {
            "name": UserRoleEnum.ADMIN,
            "display_name": "Administrator",
            "description": "Administrator bloga z pełnymi uprawnieniami",
            "color": "#dc3545",
            "permissions": [
                "comment.create", "comment.like", "comment.moderate", "comment.delete",
                "post.create", "post.edit", "post.delete", "post.publish",
                "user.manage", "role.manage", "system.admin"
            ],
            "level": 100
        }
    ]
    
    # 🏆 RANGI UŻYTKOWNIKÓW
    ranks_data = [
        {
            "name": UserRankEnum.NEWBIE,
            "display_name": "👶 Nowy użytkownik",
            "description": "Świeżo zarejestrowany użytkownik",
            "icon": "👶",
            "color": "#17a2b8",
            "requirements": {"comments": 0, "likes": 0},
            "level": 1
        },
        {
            "name": UserRankEnum.REGULAR,
            "display_name": "👤 Regularny użytkownik",
            "description": "Aktywny członek społeczności",
            "icon": "👤",
            "color": "#28a745",
            "requirements": {"comments": 5, "likes": 10},
            "level": 2
        },
        {
            "name": UserRankEnum.TRUSTED,
            "display_name": "🤝 Zaufany użytkownik",
            "description": "Doświadczony i zaufany członek",
            "icon": "🤝",
            "color": "#007bff",
            "requirements": {"comments": 25, "likes": 50},
            "level": 3
        },
        {
            "name": UserRankEnum.STAR,
            "display_name": "⭐ Gwiazda społeczności",
            "description": "Wybitny członek społeczności",
            "icon": "⭐",
            "color": "#ffc107",
            "requirements": {"comments": 100, "likes": 200},
            "level": 4
        }
    ]
    
    # Dodaj role
    for role_data in roles_data:
        existing_role = db.query(UserRole).filter(UserRole.name == role_data["name"]).first()
        if not existing_role:
            role = UserRole(**role_data)
            db.add(role)
            print(f"✅ Dodano rolę: {role_data['display_name']}")
    
    # Dodaj rangi
    for rank_data in ranks_data:
        existing_rank = db.query(UserRank).filter(UserRank.name == rank_data["name"]).first()
        if not existing_rank:
            rank = UserRank(**rank_data)
            db.add(rank)
            print(f"✅ Dodano rangę: {rank_data['display_name']}")
    
    db.commit()
    print("🎯 System ról i rang został zainicjalizowany!")

# 🔧 PRZYKŁAD UŻYCIA W ENDPOINTACH
"""
from app.models import User, UserRole, UserRank, UserRoleEnum

# Sprawdzenie uprawnień
@router.post("/admin-only")
def admin_only_endpoint(current_user: User = Depends(get_current_user)):
    if not current_user.has_permission("system.admin"):
        raise HTTPException(403, "Brak uprawnień")
    
    return {"message": "Tylko dla adminów!"}

# Sprawdzenie roli
@router.get("/user-info")
def get_user_info(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.get_display_role(),
        "rank": current_user.get_display_rank(),
        "role_color": current_user.get_role_color(),
        "rank_icon": current_user.get_rank_icon(),
        "permissions": current_user.role.permissions if current_user.role else []
    }

# Automatyczny upgrade rangi
def check_and_upgrade_rank(user: User, db: Session):
    if user.rank and user.rank.level >= 4:  # Już ma najwyższą rangę
        return
    
    # Znajdź najwyższą rangę, którą spełnia
    available_ranks = db.query(UserRank).filter(
        UserRank.is_active == True
    ).order_by(UserRank.level.desc()).all()
    
    for rank in available_ranks:
        requirements = rank.requirements
        if (user.total_comments >= requirements.get("comments", 0) and 
            user.total_likes_received >= requirements.get("likes", 0)):
            if not user.rank or rank.level > user.rank.level:
                user.rank_id = rank.id
                db.commit()
                print(f"🎉 Użytkownik {user.username} awansował na {rank.display_name}!")
                break
"""
