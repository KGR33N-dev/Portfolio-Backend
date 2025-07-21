from app.database import SessionLocal
from app.models import BlogPost

db = SessionLocal()

new_post = BlogPost(
    title="Testowy wpis",
    slug="testowy-wpis",
    content="To jest zawartość testowego posta.",
    language="pl",
    is_published=True
)

db.add(new_post)
db.commit()
db.close()
