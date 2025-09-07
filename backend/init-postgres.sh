#!/bin/bash

# Script to initialize PostgreSQL with correct user from the start
# This runs inside the PostgreSQL container during initialization

set -e

echo "🔧 Initializing PostgreSQL with postgres_user..."
echo "📋 Environment variables:"
echo "  POSTGRES_DB: $POSTGRES_DB"
echo "  POSTGRES_USER: $POSTGRES_USER"
echo "  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:0:10}... (${#POSTGRES_PASSWORD} chars)"

# Create the portfolio_user if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Ensure the user exists
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$POSTGRES_USER') THEN
            CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';
            RAISE NOTICE 'Created user: $POSTGRES_USER';
        ELSE
            RAISE NOTICE 'User already exists: $POSTGRES_USER';
        END IF;
    END
    \$\$;

    -- Grant all privileges
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
    ALTER DATABASE $POSTGRES_DB OWNER TO $POSTGRES_USER;
    
    -- Grant schema privileges
    GRANT ALL ON SCHEMA public TO $POSTGRES_USER;
    
    -- Grant default privileges for future objects
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $POSTGRES_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $POSTGRES_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $POSTGRES_USER;
    
    -- Create extension if needed
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
    -- Verification
    SELECT 'Database: ' || current_database() as info;
    SELECT 'User: ' || current_user as info;
    SELECT 'Postgres user exists: ' || CASE WHEN EXISTS(SELECT 1 FROM pg_roles WHERE rolname = '$POSTGRES_USER') THEN 'YES' ELSE 'NO' END as info;
EOSQL

echo "✅ PostgreSQL initialized with postgres_user"
