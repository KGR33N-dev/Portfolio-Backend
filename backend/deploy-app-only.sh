#!/bin/bash

# Deploy application when Docker is already installed
# Use this i# Check database health
echo "🔍 Checking database..."
timeout 120 bash -c 'until docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U portfolio_user -d portfolio_prod; do 
    echo "⏳ Waiting for database with portfolio_user..."
    sleep 3
done'

if [ $? -eq 0 ]; then
    echo "✅ Database is ready with correct user"
else
    echo "⚠️  Database not ready with portfolio_user, trying postgres fallback..."
    timeout 60 bash -c 'until docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres; do sleep 2; done'
    
    if [ $? -eq 0 ]; then
        echo "✅ Database is ready (using postgres user)"
        echo "🔧 Will fix user configuration..."
        chmod +x fix-database.sh
        ./fix-database.sh
    else
        echo "❌ Database failed to start"
        docker-compose -f docker-compose.prod.yml logs db
        exit 1
    fi
fi

# Check if we need to create initial migration
MIGRATION_FILES=$(docker-compose -f docker-compose.prod.yml exec -T app find alembic/versions -name "*.py" -not -name "__init__.py" 2>/dev/null | wc -l)

if [ "$MIGRATION_FILES" -eq 0 ]; then
    echo "📝 No migrations found - creating initial migration..."
    docker-compose -f docker-compose.prod.yml exec -T app alembic revision --autogenerate -m "Initial schema"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create migration"
        exit 1
    fi
fi

# Run database migrations
echo "📊 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T app alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed"
else
    echo "❌ Migrations failed"
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
docker-compose -f docker-compose.prod.yml exec -T app python app/create_admin.pysh was interrupted

echo "🚀 Deploying Portfolio Backend Application"
echo "=========================================="

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

# Check if user is in docker group
if ! groups | grep -q docker; then
    echo "❌ User not in docker group. Adding and restarting session needed:"
    sudo usermod -aG docker ubuntu
    echo "Please logout and login again, then run this script"
    exit 1
fi

cd /home/ubuntu/Portfolio-Backend/backend

# Generate secure passwords if not done yet
if grep -q "CHANGE_DB_PASSWORD_HERE" .env.production; then
    echo "🔑 Generating secure credentials..."
    
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
    cp .env.production .env.production.backup
    
    # Update with generated values
    sed -i "s/CHANGE_DB_PASSWORD_HERE/$DB_PASSWORD/g" .env.production
    sed -i "s/CHANGE_THIS_TO_RANDOM_64_CHAR_HEX_STRING_GENERATE_NEW/$SECRET_KEY/g" .env.production
    sed -i "s/CHANGE_TO_VERY_STRONG_PASSWORD_MIN_16_CHARS/$ADMIN_PASSWORD/g" .env.production
    
    # Set secure permissions
    chmod 600 .env.production
    
    echo "✅ Credentials configured"
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down || true

# Clean up unused packages
sudo apt autoremove -y

# Build and start services
echo "🏗️  Building application..."
docker-compose -f docker-compose.prod.yml build

echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check database health
echo "🔍 Checking database..."
timeout 60 bash -c 'until docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U postgres; do sleep 2; done'

if [ $? -eq 0 ]; then
    echo "✅ Database is ready"
else
    echo "❌ Database failed to start"
    docker-compose -f docker-compose.prod.yml logs db
    exit 1
fi

# Fix database user and run migrations
echo "� Setting up database user and running migrations..."
chmod +x fix-database.sh
./fix-database.sh

# Check application health
echo "🏥 Checking application health..."
sleep 10

if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Application is healthy"
    
    # Show application info
    echo ""
    echo "📊 Application Status:"
    docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "📋 Application URLs:"
    echo "• Health: http://localhost:8080/health"
    echo "• API Docs: http://localhost:8080/docs"
    echo "• CORS Test: http://localhost:8080/cors-test"
    
    echo ""
    echo "🔧 Next steps:"
    echo "1. Configure Nginx: ./configure-nginx-security.sh"
    echo "2. Setup DNS in Cloudflare: api.kgr33n.com → $(curl -s ifconfig.me)"
    echo "3. Install SSL: ./install-ssl.sh"
    
else
    echo "❌ Application health check failed"
    echo "📋 Checking logs:"
    docker-compose -f docker-compose.prod.yml logs app
    exit 1
fi

echo ""
echo "🎉 Application deployed successfully!"
