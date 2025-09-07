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

# Create the postgres_user if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Ensure the application user exists
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$APP_USER') THEN
            CREATE USER $APP_USER WITH PASSWORD '$APP_PASSWORD';
            RAISE NOTICE 'Created user: $APP_USER';
        ELSE
            RAISE NOTICE 'User already exists: $APP_USER';
            -- Update password in case it changed
            ALTER USER $APP_USER WITH PASSWORD '$APP_PASSWORD';
        END IF;
    END
    \$\$;

    -- Grant all privileges
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
    SELECT 'App user exists: ' || CASE WHEN EXISTS(SELECT 1 FROM pg_roles WHERE rolname = '$APP_USER') THEN 'YES' ELSE 'NO' END as info;
EOSQL

echo "✅ PostgreSQL initialized with postgres_user"
