"""Add language support and featured image

Revision ID: 003_add_language_support
Revises: 002_add_email_verification
Create Date: 2025-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_language_support'
down_revision = '002_add_email_verification'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create languages table
    op.create_table('languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('native_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_languages_code'), 'languages', ['code'], unique=True)
    
    # Add featured_image column to blog_posts
    op.add_column('blog_posts', sa.Column('featured_image', sa.String(length=500), nullable=True))
    
    # Insert default languages
    op.execute("""
        INSERT INTO languages (code, name, native_name, is_active) VALUES 
        ('en', 'English', 'English', true),
        ('pl', 'Polish', 'Polski', true)
    """)
    
    # Update existing blog posts to use 'en' if language is null or invalid
    op.execute("""
        UPDATE blog_posts 
        SET language = 'en' 
        WHERE language IS NULL OR language NOT IN ('en', 'pl')
    """)
    
    # Ensure all existing language values are valid (just in case)
    op.execute("""
        UPDATE blog_posts 
        SET language = 'en' 
        WHERE language NOT IN (SELECT code FROM languages WHERE is_active = true)
    """)
    
    # Add foreign key constraint from blog_posts.language to languages.code
    op.create_foreign_key(
        'fk_blog_posts_language',
        'blog_posts', 'languages',
        ['language'], ['code']
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_blog_posts_language', 'blog_posts', type_='foreignkey')
    
    # Remove featured_image column
    op.drop_column('blog_posts', 'featured_image')
    
    # Drop languages table
    op.drop_index(op.f('ix_languages_code'), table_name='languages')
    op.drop_table('languages')
