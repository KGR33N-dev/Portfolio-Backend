#!/bin/bash

# Clean start script for production - removes everything and starts fresh
# Use this for completely fresh deployment

echo "🧹 CLEAN START - Full reset for production deployment"
echo "=================================================="

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    echo "❌ Please run as ubuntu user"
    exit 1
fi

# Check if Docker is working
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Docker is not working. Please restart the session:"
    echo "logout, then ssh back in"
    exit 1
fi

cd /home/ubuntu/Portfolio-Backend/backend

echo "🛑 Stopping all containers..."
docker-compose -f docker-compose.prod.yml down -v --remove-orphans

echo "🗑️ Removing all portfolio volumes..."
docker volume ls | grep -E "(postgres|portfolio)" | awk '{print $2}' | xargs -r docker volume rm 2>/dev/null || true

echo "🧹 Cleaning Docker system..."
docker system prune -f

echo "🗂️ Cleaning alembic cache..."
rm -rf alembic/versions/__pycache__ 2>/dev/null || true
rm -rf app/__pycache__ 2>/dev/null || true
rm -rf app/routers/__pycache__ 2>/dev/null || true

# Generate fresh credentials if needed
if grep -q "CHANGE_DB_PASSWORD_HERE" .env.production; then
    echo "🔑 Generating fresh credentials..."
    
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SECRET_KEY=$(openssl rand -hex 32)
    ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    echo "📝 Generated credentials:"
    echo "Database Password: $DB_PASSWORD"
    echo "Secret Key: $SECRET_KEY"
    echo "Admin Password: $ADMIN_PASSWORD"
    echo ""
    echo "⚠️  SAVE THESE CREDENTIALS SECURELY!"
    echo ""
    
    # Backup original
    cp .env.production .env.production.backup 2>/dev/null || true
    
    # Update with generated values
    sed -i "s/CHANGE_DB_PASSWORD_HERE/$DB_PASSWORD/g" .env.production
    sed -i "s/CHANGE_THIS_TO_RANDOM_64_CHAR_HEX_STRING_GENERATE_NEW/$SECRET_KEY/g" .env.production
    sed -i "s/CHANGE_TO_VERY_STRONG_PASSWORD_MIN_16_CHARS/$ADMIN_PASSWORD/g" .env.production
    
    # Set secure permissions
    chmod 600 .env.production
    
    echo "✅ Credentials configured"
fi

echo "🏗️ Building fresh containers..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "🚀 Starting fresh services..."
docker-compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for database to initialize (60 seconds)..."
sleep 60

# Wait for database to be ready with proper user
echo "🔍 Waiting for database to be ready..."
timeout 120 bash -c 'until docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U portfolio_user -d portfolio_prod; do sleep 3; done'

if [ $? -ne 0 ]; then
    echo "❌ Database failed to initialize properly"
    echo "📋 Database logs:"
    docker-compose -f docker-compose.prod.yml logs db
    exit 1
fi

echo "✅ Database is ready with correct user"

# Create initial migration
echo "📝 Creating initial database migration..."
docker-compose -f docker-compose.prod.yml exec -T app alembic revision --autogenerate -m "Initial schema"

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
    echo "✅ Application is healthy and ready!"
    
    echo ""
    echo "📊 Deployment Status:"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "📋 Application URLs:"
    echo "• Health: http://localhost:8080/health"
    echo "• API Docs: http://localhost:8080/docs"
    echo "• CORS Test: http://localhost:8080/cors-test"
    
    echo ""
    echo "🔧 Next steps:"
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
echo "🎉 Clean deployment completed successfully!"
