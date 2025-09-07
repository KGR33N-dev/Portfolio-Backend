#!/bin/bash

# Nuclear reset - completely removes everything and starts from absolute zero
# This is the most aggressive cleanup possible

echo "💥 NUCLEAR RESET - Complete database and container cleanup"
echo "========================================================="
echo "⚠️  This will PERMANENTLY DELETE all data, containers, volumes, and images!"
echo "⚠️  Are you sure? Type 'yes' to continue:"
read -r confirmation

if [ "$confirmation" != "yes" ]; then
    echo "❌ Aborted"
    exit 1
fi

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    echo "❌ Please run as ubuntu user"
    exit 1
fi

cd /home/ubuntu/Portfolio-Backend/backend

echo "🛑 Stopping ALL Docker containers..."
docker stop $(docker ps -aq) 2>/dev/null || true

echo "🗑️ Removing ALL containers..."
docker rm $(docker ps -aq) 2>/dev/null || true

echo "💾 Removing ALL volumes..."
docker volume rm $(docker volume ls -q) 2>/dev/null || true

echo "🌐 Removing ALL networks..."
docker network rm $(docker network ls -q) 2>/dev/null || true

echo "🖼️ Removing ALL images..."
docker rmi $(docker images -aq) --force 2>/dev/null || true

echo "🧹 System-wide Docker cleanup..."
docker system prune -af --volumes

echo "📁 Removing local cache and temp files..."
rm -rf alembic/versions/__pycache__ 2>/dev/null || true
rm -rf app/__pycache__ 2>/dev/null || true
rm -rf app/routers/__pycache__ 2>/dev/null || true
rm -rf alembic/versions/*.py 2>/dev/null || true
rm -rf .pytest_cache 2>/dev/null || true
rm -rf __pycache__ 2>/dev/null || true

echo "� Checking existing .env.production..."
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production not found!"
    echo "Please create .env.production file first or use clean-deploy.sh"
    exit 1
fi

# Extract existing credentials
DB_PASSWORD=$(grep "POSTGRES_PASSWORD=" .env.production | cut -d= -f2)
SECRET_KEY=$(grep "SECRET_KEY=" .env.production | cut -d= -f2)
ADMIN_PASSWORD=$(grep "ADMIN_PASSWORD=" .env.production | cut -d= -f2)

echo "✅ Using existing .env.production credentials"
echo "📝 Current credentials from .env.production:"
echo "Database Password: ${DB_PASSWORD:0:10}..."
echo "Secret Key: ${SECRET_KEY:0:10}..."
echo "Admin Password: ${ADMIN_PASSWORD:0:10}..."
echo ""

echo "🏗️ Building completely fresh containers..."
docker-compose -f docker-compose.prod.yml build --no-cache --force-rm

echo "🚀 Starting fresh services..."
docker-compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for database to initialize completely (90 seconds)..."
sleep 90

# Wait for database with very long timeout
echo "🔍 Waiting for database to be ready..."
timeout 300 bash -c 'until docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U portfolio_user -d portfolio_prod; do 
    echo "⏳ Still waiting for database..."
    sleep 5
done'

if [ $? -ne 0 ]; then
    echo "❌ Database still not ready. Let's check what's happening..."
    echo "📋 Database logs:"
    docker-compose -f docker-compose.prod.yml logs db
    echo ""
    echo "📋 App logs:"
    docker-compose -f docker-compose.prod.yml logs app
    echo ""
    echo "🔧 Let's try to fix the database manually..."
    
    # Manual database fix
    docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres -d portfolio_prod -c "
    CREATE USER portfolio_user WITH PASSWORD '$DB_PASSWORD';
    GRANT ALL PRIVILEGES ON DATABASE portfolio_prod TO portfolio_user;
    ALTER DATABASE portfolio_prod OWNER TO portfolio_user;
    GRANT ALL ON SCHEMA public TO portfolio_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO portfolio_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO portfolio_user;
    " || true
fi

echo "✅ Database is ready"

# Test database connection
echo "🔍 Testing database connection..."
docker-compose -f docker-compose.prod.yml exec -T app python -c "
import asyncio
import sys
from sqlalchemy import text
from app.database import engine

async def test_connection():
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            print(f'✅ Database connection successful: {version[:50]}...')
            return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

if __name__ == '__main__':
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection test failed"
    exit 1
fi

# Create initial migration
echo "📝 Creating initial database migration..."
docker-compose -f docker-compose.prod.yml exec -T app alembic revision --autogenerate -m "Nuclear reset - initial schema"

if [ $? -ne 0 ]; then
    echo "❌ Failed to create initial migration"
    docker-compose -f docker-compose.prod.yml logs app
    exit 1
fi

# Run migrations
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T app alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Migration failed"
    docker-compose -f docker-compose.prod.yml logs app
    exit 1
fi

# Initialize default data
echo "🌱 Initializing default data..."
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

# Final health check
echo "🏥 Final health check..."
sleep 10

if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo ""
    echo "🎉 NUCLEAR RESET COMPLETED SUCCESSFULLY!"
    echo "======================================="
    echo ""
    echo "📊 Deployment Status:"
    docker-compose -f docker-compose.prod.yml ps
    echo ""
    echo "📋 Application URLs:"
    echo "• Health: http://localhost:8080/health"
    echo "• API Docs: http://localhost:8080/docs" 
    echo "• CORS Test: http://localhost:8080/cors-test"
    echo ""
    echo " Next steps:"
    echo "1. Test: ./test-deployment.sh"
    echo "2. Configure Nginx: ./configure-nginx-security.sh"
    echo "3. Setup DNS: api.kgr33n.com → $(curl -s ifconfig.me)"
    echo "4. Install SSL: ./install-ssl.sh"
    
else
    echo "❌ Application health check failed"
    echo "📋 Application logs:"
    docker-compose -f docker-compose.prod.yml logs app
    exit 1
fi

echo ""
echo "💥 Nuclear reset completed - everything is fresh and clean!"
