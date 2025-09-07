#!/bin/bash

# Nuclear reset - completely removes everything and starts from abs# Build and start containers
echo "🏗️  Building and starting containers..."
echo "📊 Build logs will show PostgreSQL initialization..."
docker-compose -f docker-compose.prod.yml up -d --build

echo "⏳ Waiting for services to initialize..."
echo "📋 Checking container status..."
sleep 10

# Verify container status
echo "🔍 Container verification:"
docker-compose -f docker-compose.prod.yml ps

# Check database initialization
echo "🔍 Database connection test:"
echo "  Testing with postgres_user (main user)..."
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "SELECT version();" 2>/dev/null || echo "  ❌ postgres_user connection failed"

echo "  Testing application connection..."
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "SELECT current_database(), current_user;" 2>/dev/null || echo "  ❌ application connection failed"

echo "🔍 Database structure verification:"
echo "  Available databases:"
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "\l" 2>/dev/null || echo "  ❌ Cannot list databases"

echo "  Available users:"
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "\du" 2>/dev/null || echo "  ❌ Cannot list users"

# Extended verification
echo "🔍 Extended database verification:"
echo "  Checking portfolio_prod database exists:"
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "SELECT datname FROM pg_database WHERE datname='portfolio_prod';" 2>/dev/null || echo "  ❌ Query failed"

echo "  Checking postgres_user exists:"
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "SELECT rolname FROM pg_roles WHERE rolname='postgres_user';" 2>/dev/null || echo "  ❌ Query failed"

echo "  Testing application database connection:"
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "SELECT 'Connection successful' as status;" 2>/dev/null || echo "  ❌ Application connection failed"

# Application logs verification
echo "🔍 Application startup logs:"
echo "  Checking last 20 lines of app logs for database connection..."
docker-compose -f docker-compose.prod.yml logs --tail=20 app 2>/dev/null || echo "  ❌ Cannot get app logs"

# Final status
echo ""
echo "🏁 Nuclear reset completed!"
echo "📋 Next steps:"
echo "  1. Check if both services are healthy: docker-compose -f docker-compose.prod.yml ps"
echo "  2. Run migrations: docker-compose -f docker-compose.prod.yml exec app alembic upgrade head"
echo "  3. Create admin user: docker-compose -f docker-compose.prod.yml exec app python app/create_admin.py"
echo "  4. Test API: curl http://localhost:8080/api/health"ro
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

# Load environment variables from .env.production
if [ -f ".env.production" ]; then
    echo "📄 Loading environment variables from .env.production..."
    export $(grep -v '^#' .env.production | xargs)
else
    echo "❌ .env.production not found!"
    exit 1
fi

echo "🧹 Starting nuclear reset - complete Docker cleanup..."

# Verification logs
echo "📋 Environment verification:"
echo "  - POSTGRES_DB: ${POSTGRES_DB:-'NOT SET'}"
echo "  - POSTGRES_USER: ${POSTGRES_USER:-'NOT SET'}"  
echo "  - App user: postgres_user"
echo "  - POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:0:10}... (${#POSTGRES_PASSWORD} chars)"
echo "  - DATABASE_URL: ${DATABASE_URL:0:30}..."

# Stop all containers
echo "🛑 Stopping all containers..."
docker stop $(docker ps -aq) 2>/dev/null || true

# Remove all containers
echo "🗑️  Removing all containers..."
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

echo "⏳ Waiting for database container to start (30 seconds)..."
sleep 30

# Wait for PostgreSQL to be ready for connections
echo "🔍 Waiting for PostgreSQL to accept connections..."
timeout 120 bash -c 'until docker-compose -f docker-compose.prod.yml exec -T db pg_isready -h localhost; do 
    echo "⏳ PostgreSQL starting up..."
    sleep 2
done'

# PostgreSQL is ready, but we need to ensure password is set properly
echo "🔑 Ensuring postgres_user has proper password authentication..."

# First, check if we can connect without password (trust mode)
if docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "SELECT 'Trust mode working' as status;" > /dev/null 2>&1; then
    echo "✅ PostgreSQL running in trust mode locally - setting password now..."
    
    # Set the password using trust mode connection
    docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "
    ALTER USER postgres_user WITH PASSWORD '$POSTGRES_PASSWORD';
    SELECT 'Password set successfully via trust mode' as result;
    " || echo "❌ Failed to set password via trust mode"
    
else
    echo "⚠️ Trust mode not working, trying alternative methods..."
fi

# Verify password authentication works for remote connections
echo "🔍 Testing password authentication for remote connections..."
if PGPASSWORD="$POSTGRES_PASSWORD" docker-compose -f docker-compose.prod.yml exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" db psql -h db -U postgres_user -d portfolio_prod -c "SELECT 'Password auth successful' as status;" > /dev/null 2>&1; then
    echo "✅ Password authentication successful!"
else
    echo "❌ Password authentication failed - forcing password reset..."
    
    # Force password reset using local trust connection
    docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "
    ALTER USER postgres_user WITH PASSWORD '$POSTGRES_PASSWORD';
    SELECT 'Password force-reset completed' as result;
    " || echo "❌ Force reset failed"
fi

# Wait for database with shorter timeout since we already set the password
echo "🔍 Final database readiness check..."
timeout 60 bash -c 'until docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres_user -d portfolio_prod; do 
    echo "⏳ Final check..."
    sleep 3
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
    
    # Manual database fix - force set password
    echo "🔑 Forcing password update for postgres_user..."
    docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres_user -d portfolio_prod -c "
    ALTER USER postgres_user WITH PASSWORD '$POSTGRES_PASSWORD';
    GRANT ALL PRIVILEGES ON DATABASE portfolio_prod TO postgres_user;
    ALTER DATABASE portfolio_prod OWNER TO postgres_user;
    GRANT ALL ON SCHEMA public TO postgres_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres_user;
    SELECT 'Password updated successfully for postgres_user' as result;
    " || true
else
    echo "✅ Database ready - password authentication should be working!"
fi

echo "✅ Database is ready"

# Test database connection directly
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
