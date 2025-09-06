"""
Utilities for automatic rank management
"""

from sqlalchemy.orm import Session, joinedload
from .models import User, UserRank

def auto_check_rank_upgrade(user_id: int, db: Session) -> dict:
    """
    Automatycznie sprawdź i awansuj użytkownika jeśli spełnia warunki
    Zwraca info o awansie lub braku zmian
    """
    try:
        # Pobierz użytkownika z obecną rangą
        user = db.query(User).options(joinedload(User.rank)).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Pobierz wszystkie aktywne rangi (od najwyższej)
        available_ranks = db.query(UserRank).filter(
            UserRank.is_active == True
        ).order_by(UserRank.level.desc()).all()
        
        # Sprawdź czy użytkownik kwalifikuje się do wyższej rangi
        for rank in available_ranks:
            requirements = rank.requirements or {}
            comments_req = requirements.get("comments", 0)
            likes_req = requirements.get("likes", 0)
            
            # Sprawdź czy spełnia wymagania
            if (user.total_comments >= comments_req and 
                user.total_likes_received >= likes_req):
                
                # Sprawdź czy to wyższa ranga niż obecna
                if not user.rank or rank.level > user.rank.level:
                    old_rank_name = user.rank.display_name if user.rank else "Brak rangi"
                    
                    # Awansuj
                    user.rank_id = rank.id
                    db.commit()
                    
                    return {
                        "success": True,
                        "upgraded": True,
                        "old_rank": old_rank_name,
                        "new_rank": rank.display_name,
                        "new_rank_icon": rank.icon,
                        "message": f"🎉 Awansowano z {old_rank_name} na {rank.display_name}!"
                    }
                else:
                    # Już ma tę rangę lub wyższą
                    break
        
        # Brak awansu
        return {
            "success": True,
            "upgraded": False,
            "current_rank": user.rank.display_name if user.rank else "Brak rangi",
            "message": "Brak awansu - kontynuuj aktywność!"
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error checking rank: {str(e)}"}

def update_user_stats(user_id: int, db: Session, action: str = "comment") -> dict:
    """
    Aktualizuj statystyki użytkownika i sprawdź awans
    action: 'comment' (dodaj komentarz) lub 'like_received' (otrzymał lajka)
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Aktualizuj statystyki
        if action == "comment":
            user.total_comments += 1
        elif action == "like_received":
            user.total_likes_received += 1
        
        db.commit()
        
        # Sprawdź awans po aktualizacji statystyk
        rank_result = auto_check_rank_upgrade(user_id, db)
        
        return {
            "success": True,
            "stats_updated": True,
            "action": action,
            "rank_check": rank_result
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error updating stats: {str(e)}"}
