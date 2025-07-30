"""Add email verification and security fields to users table

Revision ID: 002_add_email_verification
Revises: 001_initial_tables
Create Date: 2025-07-29 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_email_verification'
down_revision = '001_initial_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email verification columns
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('verification_code_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('verification_token', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('verification_expires_at', sa.DateTime(), nullable=True))
    
    # Add security columns
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), default=0))
    op.add_column('users', sa.Column('account_locked_until', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires_at', sa.DateTime(), nullable=True))
    
    # Add two-factor authentication columns (for future use)
    op.add_column('users', sa.Column('two_factor_enabled', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('two_factor_secret', sa.String(255), nullable=True))
    
    # Add account expiration for unverified accounts
    op.add_column('users', sa.Column('account_expires_at', sa.DateTime(), nullable=True))
    
    # Update existing users to have email_verified = True for backward compatibility
    op.execute("UPDATE users SET email_verified = TRUE WHERE email_verified IS NULL")


def downgrade() -> None:
    # Remove new columns
    op.drop_column('users', 'account_expires_at')
    op.drop_column('users', 'two_factor_secret')
    op.drop_column('users', 'two_factor_enabled')
    op.drop_column('users', 'password_reset_expires_at')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'account_locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'verification_expires_at')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'verification_code_hash')
    op.drop_column('users', 'email_verified')
