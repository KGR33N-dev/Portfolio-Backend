# Propozycja poprawki dla Comment model - ograniczenie do 2 poziomów

# Dodaj do Comment model:
def clean(self):
    """Validate comment nesting depth"""
    if self.parent_id:
        parent = Comment.objects.get(id=self.parent_id)
        if parent.parent_id is not None:
            raise ValidationError("Maksymalna głębokość komentarzy to 2 poziomy")

# Alternatywnie - dodaj pole depth:
depth = Column(Integer, default=0)  # 0 = główny komentarz, 1 = odpowiedź

# W create_comment endpoint - dodaj walidację:
if comment_data.parent_id:
    parent_comment = db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
    if parent_comment.parent_id is not None:
        raise HTTPException(
            status_code=400, 
            detail="Nie można odpowiadać na odpowiedzi. Maksymalnie 2 poziomy komentarzy."
        )
