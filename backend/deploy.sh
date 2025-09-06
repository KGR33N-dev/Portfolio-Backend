#!/bin/bash

# AWS Deployment Script for Portfolio Backend
# This script prepares and deploys the FastAPI backend

set -e  # Exit on error

echo "🚀 Starting Portfolio Backend deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required environment variables are set
check_env_vars() {
    echo "📋 Checking environment variables..."
    
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${RED}❌ DATABASE_URL is not set${NC}"
        echo "Example: postgresql://username:password@host:5432/dbname"
        exit 1
    fi
    
    if [ -z "$SECRET_KEY" ]; then
        echo -e "${YELLOW}⚠️  SECRET_KEY is not set. Using random key for development.${NC}"
        export SECRET_KEY=$(openssl rand -hex 32)
    fi
    
    if [ -z "$ADMIN_PASSWORD" ]; then
        echo -e "${YELLOW}⚠️  ADMIN_PASSWORD is not set. Admin user creation will be skipped.${NC}"
    fi
    
    echo -e "${GREEN}✅ Environment variables checked${NC}"
}

# Run database migrations
run_migrations() {
    echo "📊 Running database migrations..."
    docker-compose -f docker-compose.prod.yml exec web alembic upgrade head
    echo -e "${GREEN}✅ Migrations completed${NC}"
}

# Build and start the application
deploy_app() {
    echo "🏗️  Building and starting the application..."
    
    # Build the Docker image
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start the application
    docker-compose -f docker-compose.prod.yml up -d
    
    echo -e "${GREEN}✅ Application deployed successfully${NC}"
}

# Health check
health_check() {
    echo "🏥 Performing health check..."
    
    # Wait for the app to start
    sleep 10
    
    # Check if the app is responding
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Application is healthy${NC}"
    else
        echo -e "${RED}❌ Application health check failed${NC}"
        docker-compose -f docker-compose.prod.yml logs web
        exit 1
    fi
}

# Show logs
show_logs() {
    echo "📋 Showing application logs..."
    docker-compose -f docker-compose.prod.yml logs --tail=50 web
}

# Main deployment flow
main() {
    check_env_vars
    deploy_app
    health_check
    
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo "📱 Your API is running at: http://localhost:8000"
    echo "📖 API Documentation (if enabled): http://localhost:8000/api/docs"
    echo "❤️  Health Check: http://localhost:8000/api/health"
    
    read -p "Do you want to see the logs? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        show_logs
    fi
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "logs")
        show_logs
        ;;
    "health")
        health_check
        ;;
    "migrate")
        run_migrations
        ;;
    "stop")
        echo "🛑 Stopping the application..."
        docker-compose -f docker-compose.prod.yml down
        echo -e "${GREEN}✅ Application stopped${NC}"
        ;;
    "restart")
        echo "🔄 Restarting the application..."
        docker-compose -f docker-compose.prod.yml restart
        echo -e "${GREEN}✅ Application restarted${NC}"
        ;;
    *)
        echo "Usage: $0 {deploy|logs|health|migrate|stop|restart}"
        exit 1
        ;;
esac
