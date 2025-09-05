#!/bin/bash

# Database Backup Script for Portfolio Backend
# Run as cron job: 0 2 * * * /opt/portfolio-backend/scripts/backup.sh

set -e

# Configuration
BACKUP_DIR="/opt/portfolio-backend/backups"
DB_NAME="portfolio"
DB_USER="postgres" 
RETENTION_DAYS=7
DATE=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🗄️ Starting database backup..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup
BACKUP_FILE="$BACKUP_DIR/portfolio_backup_$DATE.sql"

echo "📊 Creating backup: $BACKUP_FILE"

if pg_dump -U "$DB_USER" -h localhost "$DB_NAME" > "$BACKUP_FILE"; then
    echo -e "${GREEN}✅ Backup created successfully${NC}"
    
    # Compress backup
    gzip "$BACKUP_FILE"
    echo "🗜️ Backup compressed: ${BACKUP_FILE}.gz"
    
    # Remove old backups (older than RETENTION_DAYS)
    find "$BACKUP_DIR" -name "portfolio_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "🧹 Old backups cleaned up (older than $RETENTION_DAYS days)"
    
    # Show backup info
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo "📏 Backup size: $BACKUP_SIZE"
    echo "📅 Backup date: $DATE"
    
else
    echo -e "${RED}❌ Backup failed${NC}"
    exit 1
fi

echo "✅ Backup completed successfully"
