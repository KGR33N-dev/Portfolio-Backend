#!/bin/bash

# Fix database user and run migrations
# Run this to fix the PostgreSQL user issue

echo "🔧 Fixing PostgreSQL user and database setup..."

cd /home/ubuntu/Portfolio-Backend/backend

# Check if containers are running
if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "❌ Containers are not running. Please run deploy-app-only.sh first"
    exit 1
fi

# Create portfolio_user in PostgreSQL
echo "👤 Creating portfolio_user in PostgreSQL..."
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres -d portfolio_prod -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'portfolio_user') THEN
        CREATE USER portfolio_user WITH PASSWORD '$(grep POSTGRES_PASSWORD .env.production | cut -d= -f2)';
        GRANT ALL PRIVILEGES ON DATABASE portfolio_prod TO portfolio_user;
        ALTER DATABASE portfolio_prod OWNER TO portfolio_user;
        GRANT ALL ON SCHEMA public TO portfolio_user;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO portfolio_user;
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO portfolio_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO portfolio_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO portfolio_user;
        RAISE NOTICE 'User portfolio_user created successfully';
    ELSE
        RAISE NOTICE 'User portfolio_user already exists';
    END IF;
END
\$\$;"

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL user configured"
else
    echo "❌ Failed to create PostgreSQL user"
    exit 1
fi

# Check if migrations exist
MIGRATION_FILES=$(docker-compose -f docker-compose.prod.yml exec -T app find alembic/versions -name "*.py" -not -name "__init__.py" 2>/dev/null | wc -l)

if [ "$MIGRATION_FILES" -eq 0 ]; then
    echo "📝 No migrations found - creating initial migration..."
    
    # Clean alembic state
    docker-compose -f docker-compose.prod.yml exec -T app python -c "
import os
import psycopg2
from urllib.parse import urlparse

try:
    DATABASE_URL = os.getenv('DATABASE_URL')
    result = urlparse(DATABASE_URL)
    
    conn = psycopg2.connect(
        host=result.hostname,
        port=result.port,
        user=result.username,
        password=result.password,
        database=result.path[1:]
    )
    
    with conn.cursor() as cursor:
        cursor.execute('DROP TABLE IF EXISTS alembic_version CASCADE;')
        conn.commit()
        print('✅ Alembic version table cleaned')
    
    conn.close()
except Exception as e:
    print(f'ℹ️  Info: {e}')
"

    # Create initial migration
    echo "📝 Creating initial migration..."
    docker-compose -f docker-compose.prod.yml exec -T app alembic revision --autogenerate -m "Initial schema"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create migration"
        exit 1
    fi
fi

# Run migrations
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T app alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed"
    docker-compose -f docker-compose.prod.yml logs app
    exit 1
fi

# Initialize default data
echo "🌱 Initializing default languages and roles..."
docker-compose -f docker-compose.prod.yml exec -T app python -c "
import asyncio
from app.database import init_default_languages, init_roles_and_ranks

async def init_data():
    try:
        await init_default_languages()
        print('✅ Default languages initialized')
    except Exception as e:
        print(f'ℹ️  Languages: {e}')
    
    try:
        await init_roles_and_ranks()
        print('✅ Roles and ranks initialized')
    except Exception as e:
        print(f'ℹ️  Roles: {e}')

if __name__ == '__main__':
    asyncio.run(init_data())
"

# Create admin user
echo "👤 Creating admin user..."
docker-compose -f docker-compose.prod.yml exec -T app python app/create_admin.py

echo ""
echo "🎉 Database setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Test: ./test-deployment.sh"
echo "2. Configure Nginx: ./configure-nginx-security.sh"
echo "3. Setup DNS and SSL"
