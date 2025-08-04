"""Add multilingual blog post support v2

Revision ID: 005_multilingual_posts_v2
Revises: 004_fix_language_support
Create Date: 2025-08-04 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_multilingual_posts_v2'
down_revision = '004_fix_language_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create blog_post_translations table
    op.create_table('blog_post_translations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('language_code', sa.String(length=10), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('meta_title', sa.String(length=200), nullable=True),
        sa.Column('meta_description', sa.String(length=300), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['language_code'], ['languages.code'], ),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', 'language_code', name='uq_post_language')
    )
    op.create_index(op.f('ix_blog_post_translations_title'), 'blog_post_translations', ['title'], unique=False)
    
    # Migrate existing blog_posts data to new structure
    # First, migrate existing posts to translations table (if any posts exist)
    op.execute("""
        INSERT INTO blog_post_translations (post_id, language_code, title, content, excerpt, meta_title, meta_description, created_at, updated_at)
        SELECT 
            id as post_id,
            COALESCE(language, 'pl') as language_code,
            title,
            content,
            excerpt,
            meta_title,
            meta_description,
            created_at,
            updated_at
        FROM blog_posts
        WHERE title IS NOT NULL AND content IS NOT NULL
    """)
    
    # Remove old columns from blog_posts (keep core fields)
    op.drop_column('blog_posts', 'title')
    op.drop_column('blog_posts', 'content')
    op.drop_column('blog_posts', 'excerpt')
    op.drop_column('blog_posts', 'meta_title')
    op.drop_column('blog_posts', 'meta_description')
    op.drop_column('blog_posts', 'language')


def downgrade() -> None:
    # Add back old columns to blog_posts
    op.add_column('blog_posts', sa.Column('title', sa.String(length=200), nullable=True))
    op.add_column('blog_posts', sa.Column('content', sa.Text(), nullable=True))
    op.add_column('blog_posts', sa.Column('excerpt', sa.Text(), nullable=True))
    op.add_column('blog_posts', sa.Column('meta_title', sa.String(length=200), nullable=True))
    op.add_column('blog_posts', sa.Column('meta_description', sa.String(length=300), nullable=True))
    op.add_column('blog_posts', sa.Column('language', sa.String(length=10), nullable=True))
    
    # Migrate data back (take first translation for each post)
    op.execute("""
        UPDATE blog_posts 
        SET 
            title = t.title,
            content = t.content,
            excerpt = t.excerpt,
            meta_title = t.meta_title,
            meta_description = t.meta_description,
            language = t.language_code
        FROM (
            SELECT DISTINCT ON (post_id) 
                post_id, title, content, excerpt, meta_title, meta_description, language_code
            FROM blog_post_translations 
            ORDER BY post_id, language_code
        ) t
        WHERE blog_posts.id = t.post_id
    """)
    
    # Make columns NOT NULL again
    op.alter_column('blog_posts', 'title', nullable=False)
    op.alter_column('blog_posts', 'content', nullable=False)
    
    # Drop translations table
    op.drop_index(op.f('ix_blog_post_translations_title'), table_name='blog_post_translations')
    op.drop_table('blog_post_translations')
