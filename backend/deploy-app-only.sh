#!/bin/bash

# Deploy application when Docker is already installed
# Use this if secure-deploy.sh was interrupted

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
timeout 60 bash -c 'until docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U portfolio_user -d portfolio_prod; do sleep 2; done'

if [ $? -eq 0 ]; then
    echo "✅ Database is ready"
else
    echo "❌ Database failed to start"
    docker-compose -f docker-compose.prod.yml logs db
    exit 1
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

# Create admin user
echo "👤 Creating admin user..."
docker-compose -f docker-compose.prod.yml exec -T app python app/create_admin.py

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
