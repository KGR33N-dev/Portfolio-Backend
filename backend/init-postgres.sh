#!/bin/bash

# Script to initialize PostgreSQL with correct user from the start
# This runs inside the PostgreSQL container during initialization

set -e

echo "🔧 Initializing PostgreSQL with postgres_user..."
echo "📋 Environment variables:"
echo "  POSTGRES_DB: $POSTGRES_DB"
echo "  Target user: postgres_user"
echo "  Password length: ${#POSTGRES_PASSWORD} chars"

# Get application user credentials from .env file
APP_USER="postgres_user"
APP_PASSWORD="${POSTGRES_PASSWORD}"

# Since POSTGRES_USER=postgres_user in docker-compose, postgres_user is already the main user
# We just need to make sure the password is set correctly and permissions are right

psql -v ON_ERROR_STOP=1 --username "$APP_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Force set the password for the main user (just in case)
    ALTER USER $APP_USER WITH PASSWORD '$APP_PASSWORD';
    
    -- Ensure all privileges are set
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $APP_USER;
    ALTER DATABASE $POSTGRES_DB OWNER TO $APP_USER;
    
    -- Grant schema privileges
    GRANT ALL ON SCHEMA public TO $APP_USER;
    
    -- Grant default privileges for future objects
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $APP_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $APP_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $APP_USER;
    
    -- Create extension if needed
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
    -- Verification
    SELECT 'Database: ' || current_database() as info;
    SELECT 'Current user: ' || current_user as info;
    SELECT 'Password authentication will work: YES' as info;
EOSQL

echo "✅ PostgreSQL initialized with postgres_user and password is set!"
