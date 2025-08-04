"""Fix language support implementation

Revision ID: 004_fix_language_support  
Revises: 003_add_language_support
Create Date: 2025-08-02 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_fix_language_support'
down_revision = '003_add_language_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to languages table if they don't exist
    # First, add updated_at column if it doesn't exist
    try:
        op.add_column('languages', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True))
    except Exception:
        pass  # Column already exists
    
    # Update is_active to be NOT NULL with default True
    op.execute("UPDATE languages SET is_active = true WHERE is_active IS NULL")
    op.alter_column('languages', 'is_active', 
                   existing_type=sa.Boolean(),
                   nullable=False,
                   server_default=sa.text('true'))
    
    # Insert default languages if they don't exist
    op.execute("""
        INSERT INTO languages (code, name, native_name, is_active, created_at, updated_at) 
        SELECT 'en', 'English', 'English', true, now(), now()
        WHERE NOT EXISTS (SELECT 1 FROM languages WHERE code = 'en')
    """)
    
    op.execute("""
        INSERT INTO languages (code, name, native_name, is_active, created_at, updated_at) 
        SELECT 'pl', 'Polish', 'Polski', true, now(), now()
        WHERE NOT EXISTS (SELECT 1 FROM languages WHERE code = 'pl')
    """)
    
    # Modify blog_posts.language column to be varchar(10) to match languages.code
    op.alter_column('blog_posts', 'language',
                   existing_type=sa.String(length=2),
                   type_=sa.String(length=10),
                   existing_nullable=True)
    
    # Update existing blog posts to use 'en' if language is null or invalid
    op.execute("""
        UPDATE blog_posts 
        SET language = 'en' 
        WHERE language IS NULL OR language NOT IN (SELECT code FROM languages WHERE is_active = true)
    """)
    
    # Add foreign key constraint from blog_posts.language to languages.code
    try:
        op.create_foreign_key(
            'fk_blog_posts_language',
            'blog_posts', 'languages',
            ['language'], ['code']
        )
    except Exception:
        pass  # Constraint might already exist


def downgrade() -> None:
    # Drop foreign key constraint
    try:
        op.drop_constraint('fk_blog_posts_language', 'blog_posts', type_='foreignkey')
    except Exception:
        pass
    
    # Revert blog_posts.language column back to varchar(2)
    op.alter_column('blog_posts', 'language',
                   existing_type=sa.String(length=10),
                   type_=sa.String(length=2),
                   existing_nullable=True)
    
    # Remove updated_at column if we added it
    try:
        op.drop_column('languages', 'updated_at')
    except Exception:
        pass
        
    # Allow is_active to be nullable again
    op.alter_column('languages', 'is_active',
                   existing_type=sa.Boolean(),
                   nullable=True,
                   server_default=None)
