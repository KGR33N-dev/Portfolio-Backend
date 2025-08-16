"""
Background tasks for application maintenance
"""
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User
import logging

logger = logging.getLogger(__name__)

async def cleanup_expired_accounts():
    """
    Remove unverified accounts that have expired (older than 24 hours)
    This task should be run periodically (e.g., every hour)
    """
    db = SessionLocal()
    try:
        # Find expired, unverified accounts
        expired_accounts = db.query(User).filter(
            User.email_verified == False,
            User.account_expires_at.isnot(None),
            User.account_expires_at < datetime.now(timezone.utc)
        ).all()
        
        if expired_accounts:
            logger.info(f"Found {len(expired_accounts)} expired unverified accounts to delete")
            
            for account in expired_accounts:
                logger.info(f"Deleting expired account: {account.email} (created: {account.created_at})")
                db.delete(account)
            
            db.commit()
            logger.info(f"Successfully deleted {len(expired_accounts)} expired accounts")
        else:
            logger.info("No expired accounts found for cleanup")
            
    except Exception as e:
        logger.error(f"Error during account cleanup: {str(e)}")
        db.rollback()
    finally:
        db.close()

async def cleanup_expired_verification_codes():
    """
    Clean up expired verification codes and tokens
    This helps keep the database clean and secure
    """
    db = SessionLocal()
    try:
        # Find users with expired verification codes
        expired_verifications = db.query(User).filter(
            User.verification_expires_at.isnot(None),
            User.verification_expires_at < datetime.now(timezone.utc)
        ).all()
        
        if expired_verifications:
            logger.info(f"Cleaning up {len(expired_verifications)} expired verification codes")
            
            for user in expired_verifications:
                user.verification_code_hash = None
                user.verification_token = None
                user.verification_expires_at = None
            
            db.commit()
            logger.info(f"Successfully cleaned up {len(expired_verifications)} expired verification codes")
        else:
            logger.info("No expired verification codes found for cleanup")
            
    except Exception as e:
        logger.error(f"Error during verification code cleanup: {str(e)}")
        db.rollback()
    finally:
        db.close()

async def cleanup_expired_password_resets():
    """
    Clean up expired password reset tokens
    """
    db = SessionLocal()
    try:
        # Find users with expired password reset tokens
        expired_resets = db.query(User).filter(
            User.password_reset_expires_at.isnot(None),
            User.password_reset_expires_at < datetime.now(timezone.utc)
        ).all()
        
        if expired_resets:
            logger.info(f"Cleaning up {len(expired_resets)} expired password reset tokens")
            
            for user in expired_resets:
                user.password_reset_token = None
                user.password_reset_expires_at = None
            
            db.commit()
            logger.info(f"Successfully cleaned up {len(expired_resets)} expired password reset tokens")
        else:
            logger.info("No expired password reset tokens found for cleanup")
            
    except Exception as e:
        logger.error(f"Error during password reset cleanup: {str(e)}")
        db.rollback()
    finally:
        db.close()

async def run_maintenance_tasks():
    """
    Run all maintenance tasks
    """
    logger.info("Starting maintenance tasks...")
    
    await cleanup_expired_accounts()
    await cleanup_expired_verification_codes()
    await cleanup_expired_password_resets()
    
    logger.info("Maintenance tasks completed")

# For manual execution or testing
if __name__ == "__main__":
    asyncio.run(run_maintenance_tasks())
